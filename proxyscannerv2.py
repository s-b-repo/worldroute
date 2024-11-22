import os
import requests
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(
    filename="proxy_scan_results.log",
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)

def check_proxy(ip, port=8080, protocol="http", timeout=5):
    """
    Check if an IP is a proxy by attempting a connection.
    Supports HTTP and HTTPS proxies.
    """
    try:
        proxy_url = f"{protocol}://{ip}:{port}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=timeout)
        if response.status_code == 200:
            result = f"{ip}:{port} is a working {protocol.upper()} proxy."
            logging.info(result)
            with open("successful_proxies.txt", "a") as success_file:
                success_file.write(f"{ip}:{port}\n")
            return result
        else:
            return f"{ip}:{port} responded but is not a valid proxy (Status: {response.status_code})."
    except requests.exceptions.ProxyError:
        return f"{ip}:{port} is not a proxy."
    except requests.exceptions.ConnectTimeout:
        return f"{ip}:{port} timed out."
    except Exception as e:
        return f"{ip}:{port} check failed (Error: {e})."


def scan_ips(file_path, port=8080, protocol="http", max_workers=10, batch_size=1000):
    """
    Scan a list of IPs from a large file, check if they are proxies, and resume if interrupted.
    Supports batch processing for large files.
    """
    try:
        # Clear previous successful proxies file
        open("successful_proxies.txt", "w").close()

        # Determine where to resume
        checkpoint_file = "progress.txt"
        start_index = 0
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r") as progress:
                start_index = int(progress.read().strip() or 0)
        
        print(f"Resuming from index: {start_index}")

        # Stream IPs from file and process in batches
        with open(file_path, "r") as file:
            batch = []
            current_index = 0
            
            for line in file:
                if current_index < start_index:
                    current_index += 1
                    continue
                
                batch.append(line.strip())
                current_index += 1

                if len(batch) == batch_size:
                    process_batch(batch, port, protocol, max_workers)
                    batch.clear()
                    with open(checkpoint_file, "w") as progress:
                        progress.write(str(current_index))
            
            # Process the last batch
            if batch:
                process_batch(batch, port, protocol, max_workers)
                with open(checkpoint_file, "w") as progress:
                    progress.write(str(current_index))
        
        print("Scanning completed. Results saved to 'scan_summary.txt' and logs.")
        print("Successful proxies saved to 'successful_proxies.txt'.")
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def process_batch(batch, port, protocol, max_workers):
    """
    Process a batch of IPs with concurrent scanning.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for result in executor.map(lambda ip: check_proxy(ip, port, protocol), batch):
            results.append(result)
            print(result)
    
    # Save batch results to a summary file
    with open("scan_summary.txt", "a") as summary:
        summary.write("\n".join(results) + "\n")


if __name__ == "__main__":
    # Customizable options
    ip_list_file = "ips.txt"  # Path to the file with IP addresses
    scan_port = 8080          # Port to scan (default: 8080)
    scan_protocol = "http"    # Protocol to use (http or https)
    max_threads = 10          # Number of concurrent threads
    batch_size = 1000         # Number of IPs to process per batch

    # Start the scanning process
    scan_ips(ip_list_file, port=scan_port, protocol=scan_protocol, max_workers=max_threads, batch_size=batch_size)
