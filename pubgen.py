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

def generate_all_public_ips():
    """Generator to produce all public IPv4 addresses."""
    for a in range(1, 224):            # Avoid reserved multicast (224.0.0.0 and above)
        for b in range(0, 256):
            for c in range(0, 256):
                for d in range(1, 255): # Skip .0 and .255 (reserved network and broadcast addresses)
                    ip = f"{a}.{b}.{c}.{d}"
                    if is_public_ip(ip):
                        yield ip

# Save public IPs to file in chunks, appending instead of overwriting
def save_all_public_ips(filename='all_public_ips.txt', chunk_size=1000000):
    with open(filename, 'a') as file:  # 'a' mode for appending
        count = 0
        for ip in generate_all_public_ips():
            file.write(ip + '\n')
            count += 1
            if count % chunk_size == 0:
                print(f"{count} IPs appended to {filename}...")

    print(f"Completed appending all public IPs to {filename}")

# Start the process (warning: this will be extensive)
# Uncomment the line below to run the full generation.
# save_all_public_ips()
