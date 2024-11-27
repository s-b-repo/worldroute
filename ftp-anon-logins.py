import ftplib
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

# Configuration
input_file = "ip_list.txt"  # Path to your 50GB IP list
output_file = "successful_ftp_logins.txt"  # File to store successful logins
progress_file = "scan_progress.txt"  # File to save progress
error_log_file = "error_log.txt"  # File to log errors
json_output_file = "successful_ftp_logins.json"  # File to store results in JSON
num_threads = 100  # Number of concurrent threads
ftp_timeout = 5  # Timeout in seconds for FTP connection
batch_size = 1000  # Number of IPs to process in a batch

# Regex for validating IPv4 addresses
ip_regex = re.compile(
    r'^((25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9][0-9]?)$'
)

# Logging setup
logging.basicConfig(
    filename='scanner.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Validate an IP address
def is_valid_ip(ip):
    return ip_regex.match(ip) is not None

# Load IPs in batches, excluding already processed ones
def load_ips_in_batches(file_path, processed_ips, batch_size=1000):
    with open(file_path, "r") as ip_file:
        batch = []
        for line in ip_file:
            ip = line.strip()
            if ip not in processed_ips and is_valid_ip(ip):
                batch.append(ip)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
        if batch:
            yield batch

# Function to check FTP anonymous login
def check_ftp_anonymous(ip):
    try:
        with ftplib.FTP(ip, timeout=ftp_timeout) as ftp:
            ftp.login('anonymous', 'anonymous')
            logging.info(f"Anonymous login allowed: {ip}")
            
            # Save to plain text
            with open(output_file, "a") as out_file:
                out_file.write(f"{ip}\n")
            
            # Save to JSON
            with open(json_output_file, "a") as json_file:
                json.dump({"ip": ip, "status": "anonymous login allowed"}, json_file)
                json_file.write("\n")
    except Exception as e:
        logging.error(f"Failed: {ip} ({e})")

# Main scanning process
def main():
    print("[*] Loading processed IPs...")
    processed_ips = set()
    try:
        with open(progress_file, "r") as prog_file:
            processed_ips = set(line.strip() for line in prog_file)
    except FileNotFoundError:
        pass  # No progress file yet

    print("[*] Scanning IP addresses...")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for batch in load_ips_in_batches(input_file, processed_ips, batch_size):
            for ip in batch:
                futures.append(executor.submit(check_ftp_anonymous, ip))
        
        for future in as_completed(futures):
            try:
                future.result()  # Raise exceptions if any occurred
            except Exception as e:
                logging.error(f"Error processing future: {e}")

        # Save progress
        with open(progress_file, "a") as prog_file:
            for batch in load_ips_in_batches(input_file, processed_ips, batch_size):
                prog_file.writelines(f"{ip}\n" for ip in batch)

    print("[*] Scanning complete. Results saved.")

if __name__ == "__main__":
    main()
