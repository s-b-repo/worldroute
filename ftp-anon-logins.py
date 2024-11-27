import ftplib
import logging
import json
import time
from threading import Thread, Lock
from queue import Queue
import os

# Configuration
input_file = "all_public_ips.txt"  # Path to your IP list
output_file = "successful_ftp_logins.txt"  # File to store successful logins
progress_file = "scan_progress1.txt"  # File to save progress
json_output_file = "successful_ftp_logins1.json"  # File to store results in JSON
num_threads = 50  # Number of concurrent threads
ftp_timeout = 5  # Timeout in seconds for FTP connection
connection_delay = 0.1  # Delay between FTP connections (seconds)

# Logging setup
logging.basicConfig(
    filename='scanner1.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Thread-safe operations
lock = Lock()
ip_queue = Queue()


# Function to check FTP anonymous login
def check_ftp_anonymous(ip, results):
    try:
        with ftplib.FTP(ip, timeout=ftp_timeout) as ftp:
            ftp.login('anonymous', 'anonymous')
            logging.info(f"Anonymous login allowed: {ip}")
            results.append({"ip": ip, "status": "anonymous login allowed"})
    except Exception as e:
        logging.error(f"Failed: {ip} ({e})")


# Worker thread function
def worker(ip_queue, progress_file, output_file, json_output_file):
    local_results = []
    while not ip_queue.empty():
        ip = ip_queue.get()
        check_ftp_anonymous(ip, local_results)
        ip_queue.task_done()
        if len(local_results) >= 100:  # Save progress after every 100 IPs
            save_progress(local_results, progress_file, output_file, json_output_file)
            local_results.clear()
        time.sleep(connection_delay)
    # Save remaining results
    if local_results:
        save_progress(local_results, progress_file, output_file, json_output_file)


# Progress saver
def save_progress(results, progress_file, output_file, json_output_file):
    with lock:
        with open(progress_file, "a") as prog_file:
            prog_file.write("\n".join(result['ip'] for result in results) + "\n")
        with open(output_file, "a") as out_file:
            for result in results:
                out_file.write(f"{result['ip']}\n")
        with open(json_output_file, "w") as json_file:
            json.dump(results, json_file, indent=4)


# IP generator for large files
def ip_generator(file_path, scanned_ips):
    with open(file_path, "r") as ip_file:
        for ip in ip_file:
            ip = ip.strip()
            if ip and ip not in scanned_ips:
                yield ip


# Main function
def main():
    print("[*] Starting scan...")
    try:
        # Load progress
        scanned_ips = set()
        if os.path.exists(progress_file):
            with open(progress_file, "r") as prog_file:
                scanned_ips = set(prog_file.read().splitlines())

        # Enqueue IPs
        for ip in ip_generator(input_file, scanned_ips):
            ip_queue.put(ip)

        # Start threads
        threads = []
        for _ in range(num_threads):
            thread = Thread(target=worker, args=(ip_queue, progress_file, output_file, json_output_file))
            thread.start()
            threads.append(thread)

        # Wait for threads to finish
        for thread in threads:
            thread.join()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    print("[*] Scanning complete. Results saved.")


if __name__ == "__main__":
    main()
