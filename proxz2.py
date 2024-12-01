import requests
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import time
from threading import Thread, Lock

# Set up logging
logging.basicConfig(
    filename="proxy_scan_results.log",
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)

write_lock = Lock()

def check_proxy(ip, port=8080, protocol="http", timeout=5):
    """
    Check if an IP is a proxy by attempting a connection.
    Supports HTTP and HTTPS proxies.
    """
    try:
        proxy_url = f"{protocol}://{ip}:{port}"
        proxies = {"http": proxy_url, "https": proxy_url}

        response = requests.get(
            "http://httpbin.org/ip", proxies=proxies, timeout=timeout
        )

        if response.status_code == 200:
            result = f"{ip}:{port} is a working {protocol.upper()} proxy."
            logging.info(result)

            with write_lock:
                with open("successful_proxies.txt", "a") as success_file:  # Changed to "a" for appending
                    success_file.write(f"{ip}:{port}\n")

            return result
        else:
            logging.info(f"{ip}:{port} responded with status code {response.status_code}.")
            return f"{ip}:{port} responded but is not a valid proxy (Status: {response.status_code})."
    except requests.exceptions.ProxyError:
        return f"{ip}:{port} is not a proxy."
    except requests.exceptions.ConnectTimeout:
        return f"{ip}:{port} timed out."
    except Exception as e:
        return f"{ip}:{port} check failed (Error: {e})."

def process_ip_batch(ips, port, protocol, executor, timeout):
    """
    Process a batch of IPs and check if they are proxies.
    """
    return list(executor.map(lambda ip: check_proxy(ip, port, protocol, timeout), ips))

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

def scan_ips(file_path, port=8080, protocol="http", batch_size=10000, progress_file="scan_progress.txt", timeout=5):
    """
    Scan a large list of IPs from a file in batches with progress saving.
    Optimized for very large files (e.g., 50GB).
    """
    try:
        # Do not overwrite successful proxies, open in append mode
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
                    process_ip_batch(batch, port, protocol, executor, timeout)
                    batch = []

                # Save progress every 10,000 lines
                if line_num % 10000 == 0:
                    update_progress(progress_file, line_num)
                    print(f"Processed {line_num} lines...")

            # Process any remaining IPs in the batch
            if batch:
                process_ip_batch(batch, port, protocol, executor, timeout)

            update_progress(progress_file, current_line[0])
        print("Scanning completed. Check 'successful_proxies.txt' for results.")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    ip_list_file = "all_public_ips.txt"  # Path to the large file with IP addresses
    scan_port = 8080          # Port to scan (default: 8080)
    scan_protocol = "http"    # Protocol to use (http or https)
    batch_size = 10000         # Number of IPs to process per batch
    progress_file = "scan_progress_proxy.txt"  # Progress tracking file

    scan_ips(ip_list_file, port=scan_port, protocol=scan_protocol, batch_size=batch_size, progress_file=progress_file)
