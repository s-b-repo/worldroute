import asyncio
import csv
import sys
import shlex
from asyncio import Semaphore
from pathlib import Path

MAX_CONCURRENT_TASKS = 5
WRITE_BATCH_SIZE = 100  # Number of entries to write to CSV at once

def generate_unique_filename(base_filename: str) -> str:
    counter = 1
    output_path = Path(base_filename)
    while output_path.exists():
        output_path = Path(f"{base_filename}_{counter}.csv")
        counter += 1
    return str(output_path)

async def run_routersploit(ip: str, output_csv: str, semaphore: Semaphore, buffer):
    async with semaphore:
        print(f"[INFO] Running routersploit autopwn on IP: {ip}")

        command = f"echo -e 'use scanners/autopwn\nset target {shlex.quote(ip)}\nrun\nexit\n' | python3 rsf.py"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Collecting and processing the output
        async for line in process.stdout:
            line = line.decode().strip()
            if any(keyword in line.lower() for keyword in ["vulnerable", "exploit", "success"]):
                buffer.append([ip, line])

        await process.wait()
        print(f"[INFO] Completed routersploit autopwn on IP: {ip}")

async def process_ips_concurrently(file_path: str, output_csv: str, semaphore: Semaphore):
    tasks = []
    buffer = []

    with open(file_path, "r") as file, open(output_csv, mode="a", newline="") as csv_file:
        writer = csv.writer(csv_file)

        for line in file:
            ip = line.strip()
            if ip:
                tasks.append(run_routersploit(ip, output_csv, semaphore, buffer))

            # Write batch to CSV if buffer exceeds threshold
            if len(buffer) >= WRITE_BATCH_SIZE:
                writer.writerows(buffer)
                buffer.clear()

            # Gather tasks when they reach concurrency limit
            if len(tasks) >= MAX_CONCURRENT_TASKS:
                await asyncio.gather(*tasks)
                tasks.clear()

        # Complete any remaining tasks and write final buffer
        if tasks:
            await asyncio.gather(*tasks)
        if buffer:
            writer.writerows(buffer)

    print("[INFO] Completed processing all IPs from file.")

async def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ip_list_file.txt>")
        sys.exit(1)

    ip_list_file = sys.argv[1]
    output_csv = generate_unique_filename("routersploit_vulnerable_results.csv")
    with open(output_csv, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["IP Address", "Vulnerability Details"])
    print(f"[INFO] Created CSV file with headers: {output_csv}")

    semaphore = Semaphore(MAX_CONCURRENT_TASKS)
    await process_ips_concurrently(ip_list_file, output_csv, semaphore)
    print(f"[INFO] Autopwn complete for all IPs. Vulnerabilities recorded in {output_csv}")

if __name__ == "__main__":
    asyncio.run(main())
