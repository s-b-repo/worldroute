import socket
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
        
        # Use requests to test proxy connectivity
        response = requests.get(
            "http://httpbin.org/ip", proxies=proxies, timeout=timeout
        )
        
        if response.status_code == 200:
            result = f"{ip}:{port} is a working {protocol.upper()} proxy."
            logging.info(result)
            
            # Save successful proxy to a separate file
            with open("successful_proxies.txt", "a") as success_file:
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


def scan_ips(file_path, port=8080, protocol="http", max_workers=10):
    """
    Scan a list of IPs from a file and check if they are proxies.
    Supports multiple protocols and logs results to a file.
    """
    try:
        # Clear previous successful proxies file
        open("successful_proxies.txt", "w").close()

        # Load IP addresses from file
        with open(file_path, "r") as file:
            ips = [line.strip() for line in file if line.strip()]
        
        print(f"Scanning {len(ips)} IPs on port {port} with {protocol.upper()} protocol...")
        results = []

        # Use threading for faster scanning
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for result in executor.map(lambda ip: check_proxy(ip, port, protocol), ips):
                results.append(result)
                print(result)
        
        # Save final results to a summary file
        with open("scan_summary.txt", "w") as summary:
            summary.write("\n".join(results))
        
        print("Scanning completed. Results saved to 'scan_summary.txt' and logs.")
        print("Successful proxies saved to 'successful_proxies.txt'.")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Customizable options
    ip_list_file = "ips.txt"  # Path to the file with IP addresses
    scan_port = 8080          # Port to scan (default: 8080)
    scan_protocol = "http"    # Protocol to use (http or https)
    max_threads = 10          # Number of concurrent threads
    
    # Start the scanning process
    scan_ips(ip_list_file, port=scan_port, protocol=scan_protocol, max_workers=max_threads)
