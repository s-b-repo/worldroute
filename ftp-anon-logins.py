import ftplib
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import time
from threading import Thread, Lock

# Set up logging
logging.basicConfig(
    filename="ftp_scan_results.log",
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)

write_lock = Lock()

def check_ftp_anonymous(ip, port=21, retries=3, timeout=5):
    """
    Check if an FTP server allows anonymous login with retries.
    """
    for attempt in range(retries):
        try:
            with ftplib.FTP(timeout=timeout) as ftp:
                ftp.connect(ip, port)
                ftp.login("anonymous", "")  # Attempt anonymous login

                # If login is successful, log and return success message
                result = f"{ip}:{port} allows anonymous FTP login."
                logging.info(result)

                with write_lock:
                    with open("successful_ftp.txt", "a") as success_file:  # Changed to "a" for appending
                        success_file.write(f"{ip}:{port}\n")

                return result
        except ftplib.all_errors as e:
            # If the attempt fails, log the failure and retry
            logging.info(f"Attempt {attempt + 1}/{retries} for {ip}:{port} failed to allow anonymous FTP login (Error: {e}).")
            if attempt == retries - 1:
                return f"{ip}:{port} failed to allow anonymous FTP login after {retries} attempts (Error: {e})."
            time.sleep(2)  # Wait before retrying

def process_ip_batch(ips, port, executor, retries, timeout):
    """
    Process a batch of IPs and check if they allow anonymous FTP login.
    """
    return list(executor.map(lambda ip: check_ftp_anonymous(ip, port, retries, timeout), ips))

def get_last_processed_line(progress_file):
    """
    Retrieve the last processed line number from the progress file.
    Ensures valid content is read and defaults to 0 on failure.
    """
    try:
        if os.path.exists(progress_file):
            with open(progress_file, "r") as file:
                line = file.readline().strip()
                if line.isdigit():
                    return int(line)
    except Exception as e:
        logging.warning(f"Error reading progress file: {e}")
    return 0

def update_progress(progress_file, line_num):
    """
    Update the progress file with the current line number.
    """
    try:
        with open(progress_file, "w") as file:
            file.write(f"{line_num}\n")
    except Exception as e:
        logging.warning(f"Error updating progress file: {e}")

def log_progress(current_line, total_lines):
    """
    Logs the current progress every 20 seconds in a separate thread.
    """
    while True:
        time.sleep(20)
        progress = (current_line[0] / total_lines) * 100 if total_lines else 0
        print(f"Currently processing line {current_line[0]} ({progress:.2f}%)...")

def scan_ips(file_path, port=21, retries=3, batch_size=10000, progress_file="scan_progress.txt", timeout=5):
    """
    Scan a large list of IPs from a file for FTP anonymous login with retries.
    """
    try:
        last_processed_line = get_last_processed_line(progress_file)
        print(f"Resuming from line {last_processed_line + 1}...")

        total_lines = sum(1 for _ in open(file_path, "r"))  # Total lines in file
        current_line = [last_processed_line + 1]

        # Start the progress logging thread
        progress_thread = Thread(target=log_progress, args=(current_line, total_lines), daemon=True)
        progress_thread.start()

        with open(file_path, "r", buffering=1024*1024) as file, ThreadPoolExecutor(max_workers=30) as executor:
            if last_processed_line > 0:
                # Skip lines up to the last processed line efficiently
                for _ in range(last_processed_line):
                    file.readline()

            batch = []
            for line_num, line in enumerate(file, last_processed_line + 1):
                current_line[0] = line_num  # Update current line being processed

                ip = line.strip()
                if ip:
                    batch.append(ip)

                # Process when batch reaches the configured size
                if len(batch) >= batch_size:
                    process_ip_batch(batch, port, executor, retries, timeout)
                    batch = []

                # Save progress every 10,000 lines
                if line_num % 10000 == 0:
                    update_progress(progress_file, line_num)
                    print(f"Processed {line_num} lines...")

            # Process any remaining IPs in the batch
            if batch:
                process_ip_batch(batch, port, executor, retries, timeout)

            update_progress(progress_file, current_line[0])
        print("Scanning completed. Check 'successful_ftp.txt' for results.")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    ip_list_file = "all_public_ips.txt"  # Path to the large file with IP addresses
    scan_port = 21           # FTP default port is 21
    retries = 3              # Number of retries for each FTP server
    batch_size = 10000       # Number of IPs to process per batch
    progress_file = "scan_progress_ftp.txt"  # Progress tracking file

    scan_ips(ip_list_file, port=scan_port, retries=retries, batch_size=batch_size, progress_file=progress_file)
