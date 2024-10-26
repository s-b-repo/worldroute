import re

def extract_public_ips(text):
    # Regex to match valid IPv4 addresses
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ips = re.findall(ip_pattern, text)

    # Filter only public IPs
    public_ips = [ip for ip in ips if is_public_ip(ip)]
    return public_ips

def is_public_ip(ip):
    # Convert IP address to integers for each octet
    octets = list(map(int, ip.split('.')))

    # Define private, loopback, and reserved IP ranges
    if (
        octets[0] == 10 or                                    # 10.0.0.0 - 10.255.255.255
        (octets[0] == 172 and 16 <= octets[1] <= 31) or      # 172.16.0.0 - 172.31.255.255
        (octets[0] == 192 and octets[1] == 168) or           # 192.168.0.0 - 192.168.255.255
        octets[0] == 127 or                                  # 127.0.0.0 - 127.255.255.255 (loopback)
        (octets[0] == 169 and octets[1] == 254) or           # 169.254.0.0 - 169.254.255.255 (link-local)
        (octets[0] >= 224)                                   # 224.0.0.0 - 255.255.255.255 (multicast/reserved)
    ):
        return False
    return True

def save_ips_to_file(ips, filename='public_ips.txt'):
    with open(filename, 'w') as file:
        for ip in ips:
            file.write(ip + '\n')
    print(f"Public IPs saved to {filename}")

# Example usage:
text = """
Here is a list of IPs:
192.168.1.1
10.0.0.1
8.8.8.8
172.16.0.1
203.0.113.5
127.0.0.1
169.254.0.1
"""

public_ips = extract_public_ips(text)
save_ips_to_file(public_ips)
