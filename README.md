# worldroute
autopwn a list of ip address
Explanation

    File Reading: This script reads a list of IP addresses or domain names from a file specified on the command line.
    Initializing RouterSploit Scanner: The script creates an instance of the Exploit class, which is the autopwn scanner module in RouterSploit.
    Setting Targets and Scanning: For each target in the list, it sets scanner.target and runs the scan.
    Error Handling: Basic error handling is added for file input errors and RouterSploit scanning errors.

Running the Script

Save the script as scan_alist.py, and run it from the command line:


python scan_alist.py targets.txt

Here, targets.txt should contain a list of IP addresses or domain names, each on a new line, like so:

192.168.1.1
example.com
10.0.0.1

Requirements

    Python: Ensure you’re using the same version of Python that RouterSploit supports.
    RouterSploit Installed: Install RouterSploit from its GitHub repo and make sure all dependencies are installed.

Customizing for Other Scanners

This example uses autopwn to perform generic scans. If you want to use specific modules, you can modify the Exploit class to your desired module, like scanners.router or another relevant scanner within RouterSploit’s available modules.

######
######
bash script

Explanation

    CSV Output: This script logs each IP address and successful exploit line in results.csv.
    Success Check: The script filters output for lines containing the word "success" (or similar), which is typical for RouterSploit logs when an exploit succeeds. Adjust this term based on RouterSploit's exact output.
    Quote Wrapping: Each cell in the CSV is wrapped in quotes to avoid issues with commas in exploit descriptions.

Usage

Run the script as before:

bash

./routersploit_autopwn_to_csv.sh ip_list.txt

Results Format

The routersploit_results.csv file will look like this:


IP Address,Successful Exploit
192.168.1.1,"Exploit XYZ successful on port 80"
192.168.1.2,"Exploit ABC successful on port 443"

This CSV can then be imported directly into any spreadsheet software for further analysis.
