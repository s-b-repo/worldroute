import ftplib
import threading
import json
import re
from queue import Queue

# Configuration
input_file = "ip_list.txt"  # Path to your 50GB IP list
output_file = "successful_ftp_logins.txt"  # File to store successful logins
progress_file = "scan_progress.txt"  # File to save progress
error_log_file = "error_log.txt"  # File to log errors
json_output_file = "successful_ftp_logins.json"  # File to store results in JSON
num_threads = 100  # Number of concurrent threads
ftp_timeout = 5  # Timeout in seconds for FTP connection

# Thread-safe queues
ip_queue = Queue()
lock = threading.Lock()

# Regex for validating IPv4 addresses
ip_regex = re.compile(
    r'^((25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$'
)

# Validate an IP address
def is_valid_ip(ip):
    return ip_regex.match(ip) is not None

# Load IPs, excluding already processed ones
def load_ips(file_path, progress_path):
    processed_ips = set()
    # Read already processed IPs from progress file
    try:
        with open(progress_path, "r") as prog_file:
            processed_ips = set(line.strip() for line in prog_file)
    except FileNotFoundError:
        pass  # Progress file doesn't exist yet, proceed with all IPs

    # Load valid IPs that are not already processed
    with open(file_path, "r") as ip_file:
        for line in ip_file:
            ip = line.strip()
            if ip not in processed_ips and is_valid_ip(ip):
                ip_queue.put(ip)

# Function to check FTP anonymous login
def check_ftp_anonymous(ip):
    try:
        with ftplib.FTP(ip, timeout=ftp_timeout) as ftp:
            ftp.login('anonymous', 'anonymous')
            with lock:
                print(f"[+] Anonymous login allowed: {ip}")
                # Save to plain text
                with open(output_file, "a") as out_file:
                    out_file.write(f"{ip}\n")
                # Save to JSON
                with open(json_output_file, "a") as json_file:
                    json.dump({"ip": ip, "status": "anonymous login allowed"}, json_file)
                    json_file.write("\n")
    except Exception as e:
        with lock:
            print(f"[-] Failed: {ip} ({e})")
            with open(error_log_file, "a") as error_file:
                error_file.write(f"{ip}: {e}\n")

# Worker thread
def worker():
    while not ip_queue.empty():
        ip = ip_queue.get()
        try:
            check_ftp_anonymous(ip)
        finally:
            with lock:
                # Save progress
                with open(progress_file, "a") as prog_file:
                    prog_file.write(f"{ip}\n")
            ip_queue.task_done()

def main():
    # Load IP addresses, excluding already processed ones
    print("[*] Loading IP addresses...")
    load_ips(input_file, progress_file)
    
    # Create and start threads
    print(f"[*] Starting threads with {num_threads} workers...")
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    # Wait for all threads to finish
    for t in threads:
        t.join()

    print("[*] Scanning complete. Results saved.")

if __name__ == "__main__":
    main()
