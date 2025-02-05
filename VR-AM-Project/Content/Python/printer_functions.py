import subprocess
from threading import Thread
import re
import json
import time
import unreal
import os

def executeTerminal(command):
    os.system(command)

parsed_entries = {}
buffered_lines = []
extracted_data = []

def parse_console_output(process):
    global parsed_entries, buffered_lines, extracted_data
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

            extracted_data = []

            # Print schedule extraction
            if 1001 in parsed_entries:
                data = parsed_entries[1001]["data"]
                if isinstance(data, dict):
                    time_val = int(data.get("time", 0))
                    total_time_val = int(data.get("totalTime", 0))
                    progress_val = int(data.get("progress", 0) / 100) 
                    extracted_data.extend([time_val, total_time_val, progress_val])

            # Nozzle and hotbed temperatures
            for key in (1003, 1004):  # nozzle_temp and hotbed_temp
                if key in parsed_entries:
                    data = parsed_entries[key]["data"]
                    if isinstance(data, dict):
                        current_temp = int(data.get("currentTemp", 0) / 100) 
                        target_temp = int(data.get("targetTemp", 0) /100)
                        extracted_data.extend([current_temp, target_temp])

            # Print speed extraction
            if 1006 in parsed_entries:
                data = parsed_entries[1006]["data"]
                if isinstance(data, dict):
                    print_speed_val = int(data.get("value", 0))
                    extracted_data.append(print_speed_val)
            
        except Exception:
            pass


def start_subprocess():
    return subprocess.Popen(
        ["python3", "C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py", "mqtt", "monitor"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

def monitor_and_collect_data():
    executeTerminal(f"python3 C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py pppp lan-search -s") #update IP
    global process
    process = start_subprocess()
    while process.poll() is None:
        parse_console_output(process)
        time.sleep(1)

@unreal.uclass()
class PrinterFunctions(unreal.BlueprintFunctionLibrary):

    @unreal.ufunction(static = True, params = [str], ret = bool)
    def PrintFile(FilePath):
        Thread(target=executeTerminal, args=(f"python3 C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py pppp print-file {FilePath}", )).start()
        return True
    
    @unreal.ufunction(static=True, params=[], ret=bool)
    def MonitorPrinting():
        Thread(target=monitor_and_collect_data).start()
        return True

    @unreal.ufunction(static=True, params=[], ret=bool)
    def StopMonitor():
        try:
            process.kill()
        except:
            pass
        return True

    #Get Current temps
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetNozzoleTemp():
        return extracted_data[3]

    @unreal.ufunction(static=True, params=[], ret=int)
    def GetHotbedTemp():
        return extracted_data[5]

    #Get Target temps
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetTargetNozzoleTemp():
        return extracted_data[4]

    @unreal.ufunction(static=True, params=[], ret=int)
    def GetTargetHotbedTemp():
        return extracted_data[6]

    #Get Times
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetTimeValue():
        return extracted_data[0]

    @unreal.ufunction(static=True, params=[], ret=int)
    def GetTotalTimeValue():
        return extracted_data[1]

#time_val - 0
#total_time_val - 1
#progress_val - 2
#current_temp_nozzle - 3
#target_temp_nozzle b- 4
#current_temp_hotbed - 5
#target_temp_hotbed - 6




