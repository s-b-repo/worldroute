import subprocess
import concurrent.futures
import requests
from openpyxl import Workbook

# Verify proxy by making an HTTP request through the IP and port
def verify_proxy(ip, port):
    proxy = { "http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}" }
    try:
        response = requests.get("http://www.google.com", proxies=proxy, timeout=5)
        # If the request is successful, assume it's a working proxy
        if response.status_code == 200:
            return True
    except requests.RequestException:
        pass
    return False

# Run nmap on a single IP to check for proxy ports
def scan_ip(ip):
    try:
        # Run nmap for common proxy ports and look for open ones
        result = subprocess.run(
            ["nmap", "-p80,1080,3128,8080,443", "--open", ip],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Check for open ports in the result
        open_ports = []
        for line in result.stdout.splitlines():
            if "/tcp" in line and "open" in line:
                port = int(line.split("/")[0])
                if verify_proxy(ip, port):
                    open_ports.append(port)
        
        if open_ports:
            return f"{ip} is a proxy, open ports: {open_ports}"
        else:
            return f"{ip} is not a proxy"
    except subprocess.TimeoutExpired:
        return f"{ip} scan timed out"

# Run scans on a list of IPs in parallel
def scan_ips(ip_list):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(scan_ip, ip_list))
    return results

# Read IPs from a file
with open("ip_list.txt", "r") as file:
    ip_list = [line.strip() for line in file if line.strip()]

# Scan IPs and collect results
results = scan_ips(ip_list)

# Save results to an Excel file
wb = Workbook()
ws = wb.active
ws.append(["IP Address", "Result"])

for ip, result in zip(ip_list, results):
    ws.append([ip, result])

wb.save("proxy_scan_results.xlsx")
