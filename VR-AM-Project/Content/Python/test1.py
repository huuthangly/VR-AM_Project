import subprocess
from threading import Thread
import re
import json
import time
import os

parsed_entries = {}
buffered_lines = []
extracted_data = [0, 0, 0, 0, 0, 0, 0, 0]
process = None

def executeTerminal(command):
    os.system(command)

def parse_console_output(process):
    global parsed_entries, buffered_lines
    for line in iter(process.stdout.readline, ''):
        line = line.strip()
        if not line:
            continue

        buffered_lines.append(line)
        combined_data = " ".join(buffered_lines)

        try:
            # Structured entry like [1001] print_schedule {...}
            match = re.search(r"\[(\d+)\]\s+(\w+)\s+(.*)", combined_data)
            if match:
                key = int(match.group(1))
                label = match.group(2)
                data_str = match.group(3).strip()

                try:
                    data = json.loads(data_str.replace("'", "\""))
                except json.JSONDecodeError:
                    if data_str.endswith("}") and data_str.count("{") == data_str.count("}") :
                        data = data_str
                    else:
                        continue

                parsed_entries[key] = {"label": label, "data": data}
                buffered_lines.clear()
                continue

            # Unstructured JSON fragments
            if combined_data.startswith("{") and combined_data.endswith("}"):
                data = json.loads(combined_data.replace("'", "\""))
                parsed_entries["unstructured"] = {"label": None, "data": data}
                buffered_lines.clear()
        except Exception:
            pass
   
def parse_extracted_data():
    global parsed_entries, extracted_data

    # Print schedule extraction
    if 1001 in parsed_entries:
        data = parsed_entries[1001]["data"]
        if isinstance(data, dict):
            extracted_data[0] = int(data.get("time", 0))
            extracted_data[1] = int(data.get("totalTime", 0))
            extracted_data[2] = int(data.get("progress", 0) / 100) 
            # extracted_data.extend([time_val, total_time_val, progress_val])
     #else:
        # extracted_data.extend([0, 0, 0])

    # Nozzle and hotbed temperatures
    counter = 3
    for key in (1003, 1004):  # nozzle_temp and hotbed_temp
        if key in parsed_entries:
            data = parsed_entries[key]["data"]
            if isinstance(data, dict):
                extracted_data[counter] = int(data.get("currentTemp", 0) / 100) 
                counter = counter + 1
                extracted_data[counter] = int(data.get("targetTemp", 0) /100)
                counter = counter + 1
                # extracted_data.extend([current_temp, target_temp])
        # else:
           # extracted_data.extend([0, 0])

    # Print speed extraction
    if 1006 in parsed_entries:
        data = parsed_entries[1006]["data"]
        if isinstance(data, dict):
            extracted_data[7] = int(data.get("value", 0))
           # extracted_data.append(print_speed_val)
    #else:
        #extracted_data.extend([0])
    
def start_subprocess():
    return subprocess.Popen(
        ["python3", "C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py", "mqtt", "monitor"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

def monitor_and_collect_data():
    """Runs the subprocess and extracts data."""
    executeTerminal(f"python3 C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py pppp lan-search -s") #update IP
    global process
    process = start_subprocess()
    parse_console_output(process)
    while process.poll() is None:
        parse_extracted_data()
        unreal.log_warning("Hello 6")
        time.sleep(1)

def print_extracted_data():
    """Prints the current contents of the extracted_data list."""
    print("Extracted Data:", extracted_data)