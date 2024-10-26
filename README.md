Worldroute - Automated IP Address Scanning and Exploitation

worldroute is a Python and Bash-based automation project for scanning and exploiting vulnerabilities across a list of IP addresses using RouterSploit's autopwn scanner. The project includes two main scripts: a Python script for executing scans and a Bash script to export results in CSV format for easy analysis.
Features

    IP/DNS List Input: Reads a list of IP addresses or domain names from a specified text file.
    RouterSploit Scanner Integration: Initializes and runs RouterSploit's autopwn scanner on each target IP.
    Error Handling: Provides basic error handling for missing files and RouterSploit scanning errors.
    Results Logging: Logs successful exploits to a CSV file for easy import into spreadsheet tools.
    IP Filtering: Filters out private IP addresses, ensuring only public IPs are scanned.

Getting Started
Prerequisites

    Python: Ensure compatibility with RouterSploit's supported Python version.
    RouterSploit: Clone and install RouterSploit from its GitHub repository. Be sure all dependencies are installed.

Script 1: scan_alist.py

This Python script scans each IP address or domain name in a list using RouterSploit's autopwn module.
Usage

Save the script as scan_alist.py and run it as follows:

#bash

python scan_alist.py targets.txt

Input Format
targets.txt should contain a list of IP addresses or domain names, each on a new line. Example:

192.168.1.1
example.com
10.0.0.1

Script 2: routersploit_autopwn_to_csv.sh

This Bash script filters successful exploits from RouterSploit’s output and logs them in a CSV format for further analysis.
Usage

Run the script with a list of IPs as follows:

bash

./routersploit_autopwn_to_csv.sh ip_list.txt

The results will be saved to routersploit_results.csv with the format:

plaintext

IP Address,Successful Exploit
192.168.1.1,"Exploit XYZ successful on port 80"
192.168.1.2,"Exploit ABC successful on port 443"

Customization
Scanner Modules

The Python script uses the autopwn module for broad scans. To target specific vulnerabilities, replace the Exploit class with any specific module from RouterSploit, such as scanners.router or another preferred module.
CSV Formatting

By default, each cell in the CSV output is wrapped in quotes to prevent comma issues with exploit descriptions. If RouterSploit’s output format changes, update the success filter as needed.
Filtering Public IPs

A helper function is_public_ip() filters out private, reserved, and special-use IP addresses, including:

    Private Ranges: 10.x.x.x, 172.16.x.x - 172.31.x.x, 192.168.x.x
    Loopback: 127.x.x.x
    Link-Local: 169.254.x.x
    Multicast and Reserved: 224.x.x.x - 255.x.x.x

Run the filter script to create a new file, public_ips.txt, containing only public IPs for scanning.
Contribution

Feel free to suggest improvements, report issues, or contribute new features!
