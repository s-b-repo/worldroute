import nmap
import pandas as pd
import concurrent.futures

# List of firewall evasion techniques
FIREWALL_EVASION_OPTIONS = [
    "--mtu 8",  # Fragmentation for packet payloads
    "--scan-delay 50ms",  # Add a delay between probes
    "--data-length 50",  # Append random data to packets
    "-f",  # Enable packet fragmentation
]

def perform_scan(ip, evasion_method):
    """
    Perform a full port and service scan with an evasion technique on a given IP address.
    """
    scanner = nmap.PortScanner()
    results = []
    try:
        print(f"[INFO] Scanning {ip} with evasion method: {evasion_method}")
        scanner.scan(
            hosts=ip,
            arguments=f"-p- -sS -sV --open {evasion_method}",
            timeout=600  # Adjust timeout as needed
        )
        if ip in scanner.all_hosts():
            for port in scanner[ip].all_tcp():
                service_info = scanner[ip]["tcp"][port]
                results.append({
                    "IP": ip,
                    "Port": port,
                    "Service": service_info.get("name", "unknown"),
                    "Version": service_info.get("version", "unknown")
                })
        else:
            results.append({"IP": ip, "Port": "None", "Service": "None", "Version": "None"})
    except Exception as e:
        print(f"[ERROR] Failed to scan {ip}. Error: {e}")
        results.append({"IP": ip, "Port": "Error", "Service": "Error", "Version": str(e)})
    return results

def scan_ips_line_by_line(file_path, output_file, max_workers=5, batch_size=100):
    """
    Scans IPs line by line from a large file and saves results incrementally.
    """
    all_results = []
    batch_results = []
    with open(file_path, "r") as file:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for idx, line in enumerate(file):
                ip = line.strip()
                if not ip:
                    continue
                evasion_method = FIREWALL_EVASION_OPTIONS[idx % len(FIREWALL_EVASION_OPTIONS)]
                futures.append(executor.submit(perform_scan, ip, evasion_method))

                # Process results in batches
                if len(futures) >= batch_size:
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            results = future.result()
                            batch_results.extend(results)
                        except Exception as e:
                            print(f"[ERROR] Exception occurred: {e}")
                    futures.clear()
                    all_results.extend(batch_results)
                    save_results_to_spreadsheet(batch_results, output_file, append=True)
                    batch_results = []

            # Process remaining futures
            for future in concurrent.futures.as_completed(futures):
                try:
                    results = future.result()
                    batch_results.extend(results)
                except Exception as e:
                    print(f"[ERROR] Exception occurred: {e}")
            all_results.extend(batch_results)
            save_results_to_spreadsheet(batch_results, output_file, append=True)
    return all_results

def save_results_to_spreadsheet(results, output_file, append=False):
    """
    Saves scan results into a spreadsheet.
    If append is True, it appends to an existing file.
    """
    df = pd.DataFrame(results)
    if append and os.path.exists(output_file):
        existing_df = pd.read_excel(output_file)
        df = pd.concat([existing_df, df], ignore_index=True)
    df.to_excel(output_file, index=False)
    print(f"[INFO] Results saved to {output_file}")

if __name__ == "__main__":
    # Input file path and output file name
    input_file = "ip_list.txt"  # Text file containing 1 IP per line
    output_file = "scan_results.xlsx"  # Spreadsheet to save results

    # Perform scans line by line
    print("[INFO] Starting scans...")
    scan_ips_line_by_line(input_file, output_file)
