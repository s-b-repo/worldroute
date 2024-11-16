import asyncio
import csv
import ipaddress
import logging
import shlex
import sys
from asyncio import Semaphore
from pathlib import Path
from aiofiles import open as aio_open
from aiofiles.csv import writer as async_csv_writer

# Configuration
MAX_CONCURRENT_TASKS = 30
WRITE_BATCH_SIZE = 100  # Number of entries to write to CSV at once

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def validate_ip(ip: str) -> bool:
    """Validate if a string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def generate_unique_filename(base_filename: str) -> str:
    """Generate a unique filename by appending a counter if the file exists."""
    counter = 1
    output_path = Path(base_filename)
    while output_path.exists():
        output_path = Path(f"{base_filename}_{counter}.csv")
        counter += 1
    return str(output_path)

async def run_routersploit(ip: str, semaphore: Semaphore, buffer: list):
    """Run routersploit autopwn for a given IP and collect confirmed vulnerabilities."""
    async with semaphore:
        logging.info(f"Running routersploit autopwn on IP: {ip}")

        command = (
            f"echo -e 'use scanners/autopwn\nset target {shlex.quote(ip)}\nrun\nexit\n' | "
            f"python3 {Path(__file__).parent / 'rsf.py'}"
        )
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Collecting and processing output
            async for line in process.stdout:
                line = line.decode().strip()

                # Only consider lines indicating confirmed vulnerability
                if "Target is vulnerable" in line or "Device is vulnerable" in line:
                    buffer.append([ip, line])

                # Exclude lines indicating "not vulnerable"
                if "is not vulnerable" in line:
                    logging.info(f"Excluding non-vulnerable IP: {ip} ({line})")

            await process.wait()

            if process.returncode != 0:
                stderr = await process.stderr.read()
                logging.error(f"Command failed for IP {ip}: {stderr.decode()}")
        except Exception as e:
            logging.error(f"Unexpected error for IP {ip}: {e}")
        finally:
            process.kill()
            logging.info(f"Completed routersploit autopwn on IP: {ip}")

async def process_ips_concurrently(file_path: str, output_csv: str, semaphore: Semaphore):
    """Process IP addresses from a file concurrently, writing results to a CSV file."""
    buffer = []

    async with aio_open(output_csv, mode="a", newline="") as file:
        async_writer = async_csv_writer(file)

        async with aio_open(file_path, mode="r") as input_file:
            tasks = []

            async for line in input_file:
                ip = line.strip()
                if ip and validate_ip(ip):
                    tasks.append(run_routersploit(ip, semaphore, buffer))

                # Write batch to CSV if buffer exceeds threshold
                if len(buffer) >= WRITE_BATCH_SIZE:
                    await async_writer.writerows(buffer)
                    buffer.clear()

                # Gather tasks when they reach concurrency limit
                if len(tasks) >= MAX_CONCURRENT_TASKS:
                    await asyncio.gather(*tasks)
                    tasks.clear()

            # Complete any remaining tasks and write final buffer
            if tasks:
                await asyncio.gather(*tasks)
            if buffer:
                await async_writer.writerows(buffer)

    logging.info("Completed processing all IPs from file.")

async def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <ip_list_file.txt>")
        sys.exit(1)

    ip_list_file = sys.argv[1]
    output_csv = generate_unique_filename("routersploit_vulnerable_results.csv")
    
    # Create the CSV file with headers
    async with aio_open(output_csv, mode="w", newline="") as file:
        async_writer = async_csv_writer(file)
        await async_writer.writerow(["IP Address", "Vulnerability Details"])

    logging.info(f"Created CSV file with headers: {output_csv}")

    semaphore = Semaphore(MAX_CONCURRENT_TASKS)
    await process_ips_concurrently(ip_list_file, output_csv, semaphore)
    logging.info(f"Autopwn complete for all IPs. Vulnerabilities recorded in {output_csv}")

if __name__ == "__main__":
    asyncio.run(main())
