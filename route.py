from routersploit.modules.scanners.autopwn import Exploit
import sys

def scan_alist(filename):
    # Check if the filename is specified
    try:
        with open(filename, 'r') as file:
            targets = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # Initialize RouterSploit's Exploit scanner
    scanner = Exploit()

    for target in targets:
        print(f"\n[+] Scanning target: {target}")
        
        # Set the target IP or domain
        scanner.target = target
        
        # Run the scan
        try:
            scanner.run()
        except Exception as e:
            print(f"Error scanning {target}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scan_alist.py <targets_file>")
        sys.exit(1)

    filename = sys.argv[1]
    scan_alist(filename)
