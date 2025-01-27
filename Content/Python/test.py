import subprocess
import threading
import re
import json

# Dictionary to store the latest parsed entries
parsed_entries = {}

def parse_console_output(process):
    global parsed_entries
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        
        # Match the structured parts of the output
        match = re.search(r"\[(\d+)\]\s+(\w+)\s+(.*)", line)
        if match:
            key = int(match.group(1))  # Number in brackets
            label = match.group(2)  # Text label
            try:
                data = json.loads(match.group(3).strip())  # JSON-like data
            except json.JSONDecodeError:
                data = match.group(3).strip()  # Fallback to raw string if JSON fails
            
            # Update the dictionary with the latest entry
            parsed_entries[key] = {"label": label, "data": data}
        else:
            # Attempt to parse as a plain JSON object
            try:
                data = json.loads(line)
                # Use a fixed key for unstructured JSON data
                parsed_entries["unstructured"] = {"label": None, "data": data}
            except json.JSONDecodeError:
                # Use a fixed key for raw lines
                parsed_entries["unstructured"] = {"label": None, "data": line}

# Start the subprocess
process = subprocess.Popen(
    ["python3", "C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py", "mqtt", "monitor"],  # Replace with your actual command
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line-buffered
)

# Run the parser in a separate thread
thread = threading.Thread(target=parse_console_output, args=(process,))
thread.start()

# Monitor or process parsed entries
import time
while process.poll() is None:  # While the subprocess is running
    print("Latest Parsed Entries:")
    for key, entry in parsed_entries.items():
        print(f"{key}: {entry}")
    time.sleep(1)  # Adjust polling interval as needed

print("Subprocess finished!")


