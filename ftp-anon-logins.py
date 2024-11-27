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
progress_file = "scan_progress.txt"  # File to save progress
json_output_file = "successful_ftp_logins.json"  # File to store results in JSON
num_threads = 10  # Reduce thread count to minimize memory usage
ftp_timeout = 5  # Timeout in seconds for FTP connection
connection_delay = 0.1  # Delay between FTP connections (seconds)
batch_size = 1000  # Number of IPs processed per batch

# Logging setup
logging.basicConfig(
    filename='scanner.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Set to DEBUG for detailed logs
)

# Thread-safe operations
lock = Lock()
ip_queue = Queue(maxsize=batch_size)  # Limit queue size


# Function to check FTP anonymous login
def check_ftp_anonymous(ip, results):
    try:
        with ftplib.FTP(ip, timeout=ftp_timeout) as ftp:
            ftp.login('anonymous', 'anonymous')
            logging.info(f"Anonymous login allowed: {ip}")
            results.append({"ip": ip, "status": "anonymous login allowed"})
    except Exception as e:
        logging.debug(f"Failed: {ip} ({e})")


# Worker thread function
def worker(ip_queue, progress_file, output_file, json_output_file):
    local_results = []
    while True:
        ip = ip_queue.get()
        if ip is None:  # Sentinel value to signal termination
            break
        try:
            check_ftp_anonymous(ip, local_results)
        except Exception as e:
            logging.error(f"Worker encountered an error: {e}")
        finally:
            ip_queue.task_done()
            time.sleep(connection_delay)

        if len(local_results) >= 100:  # Save progress after every 100 results
            save_progress(local_results, progress_file, output_file, json_output_file)
            local_results.clear()
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
        with open(json_output_file, "a") as json_file:  # Append to avoid overwriting
            json.dump(results, json_file, indent=4)


# Main function
def main():
    logging.info("[*] Starting scan...")
    try:
        # Load progress
        scanned_ips = set()
        if os.path.exists(progress_file):
            with open(progress_file, "r") as prog_file:
                scanned_ips = set(prog_file.read().splitlines())

        # Start threads
        threads = []
        for _ in range(num_threads):
            thread = Thread(target=worker, args=(ip_queue, progress_file, output_file, json_output_file))
            thread.start()
            threads.append(thread)

        # Process IPs in batches
        with open(input_file, "r") as ip_file:
            batch = []
            for line in ip_file:
                ip = line.strip()
                if ip and ip not in scanned_ips:
                    batch.append(ip)
                    if len(batch) >= batch_size:
                        enqueue_batch(batch)
                        batch = []
            # Enqueue remaining IPs
            if batch:
                enqueue_batch(batch)

        # Signal threads to terminate
        for _ in range(num_threads):
            ip_queue.put(None)  # Sentinel value

        # Wait for threads to finish
        for thread in threads:
            thread.join()

    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("[*] Scanning complete. Results saved.")
        logging.shutdown()


# Enqueue batch of IPs
def enqueue_batch(batch):
    for ip in batch:
        ip_queue.put(ip)
    ip_queue.join()  # Wait for all items in the queue to be processed


if __name__ == "__main__":
    main()
