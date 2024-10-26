import threading

def is_public_ip(ip):
    octets = list(map(int, ip.split('.')))
    if (
        octets[0] == 10 or
        (octets[0] == 172 and 16 <= octets[1] <= 31) or
        (octets[0] == 192 and octets[1] == 168) or
        octets[0] == 127 or
        (octets[0] == 169 and octets[1] == 254) or
        (octets[0] >= 224)
    ):
        return False
    return True

def generate_ip_range(start, end, output_list):
    """Generate IPs in the specified range and add to the shared list."""
    for a in range(start, end):
        for b in range(256):
            for c in range(256):
                for d in range(1, 255):  # Skip .0 and .255
                    ip = f"{a}.{b}.{c}.{d}"
                    if is_public_ip(ip):
                        output_list.append(ip)

def save_all_public_ips(filename='all_public_ips.txt', chunk_size=1000000):
    """Generate public IPs using threads and save them in chunks to a file."""
    num_threads = 8  # Adjust based on CPU cores for optimal performance
    step = 223 // num_threads  # Divide IP range among threads
    threads = []
    output_lists = [[] for _ in range(num_threads)]  # Separate lists for each thread

    # Start threads to generate IP ranges
    for i in range(num_threads):
        start = i * step + 1
        end = start + step if i < num_threads - 1 else 224
        thread = threading.Thread(target=generate_ip_range, args=(start, end, output_lists[i]))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Combine results from all threads and save in chunks
    count = 0
    with open(filename, 'a') as file:
        buffer = []
        for output_list in output_lists:
            for ip in output_list:
                buffer.append(ip)
                count += 1
                if count % chunk_size == 0:
                    file.write('\n'.join(buffer) + '\n')
                    buffer = []  # Reset buffer
                    print(f"{count} IPs appended to {filename}...")  # Progress update
        
        # Write any remaining IPs in the buffer
        if buffer:
            file.write('\n'.join(buffer) + '\n')

    print(f"Completed appending all public IPs to {filename}")

# Uncomment to run the process
save_all_public_ips()
