import subprocess
from threading import Thread
import re
import json
import time
import unreal
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

        unreal.log(line)
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
        except Exception as e:
            unreal.log_warning(f"Exception in parse_console_output: {e}")
   
def parse_extracted_data():
    global parsed_entries, extracted_data

    # Print schedule extraction
    if 1001 in parsed_entries:
        data = parsed_entries[1001]["data"]
        if isinstance(data, dict):
            extracted_data[0] = int(data.get("time", 0))
            extracted_data[1] = int(data.get("totalTime", 0))
            extracted_data[2] = int(data.get("progress", 0) / 100) 

    # Nozzle and hotbed temperatures
    counter = 3
    for key in (1003, 1004):  # nozzle_temp and hotbed_temp
        if key in parsed_entries:
            data = parsed_entries[key]["data"]
            if isinstance(data, dict):
                extracted_data[counter] = int(data.get("currentTemp", 0) / 100) 
                counter += 1
                extracted_data[counter] = int(data.get("targetTemp", 0) /100)
                counter += 1

    # Print speed extraction
    if 1006 in parsed_entries:
        data = parsed_entries[1006]["data"]
        if isinstance(data, dict):
            extracted_data[7] = int(data.get("value", 0))
    
def start_subprocess():
    return subprocess.Popen(
        ["python3", "C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py", "mqtt", "monitor"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

def monitor_and_collect_data():
    """Runs the subprocess and extracts data."""
    executeTerminal(f"python3 C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py pppp lan-search -s") #update IP
    global process
    process = start_subprocess()
    thread = Thread(target=parse_console_output, args=(process,))
    thread.start()
    
    while process.poll() is None:
        parse_extracted_data()
        unreal.log_warning("Process is Running")
        time.sleep(1)
    
    unreal.log_warning(f"Process is not Running, code: {process.poll()}")

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
        global process, parsed_entries, buffered_lines, extracted_data
        try:
            if process:
                process.kill()

            parsed_entries = {}
            buffered_lines = []
            extracted_data = [0, 0, 0, 0, 0, 0, 0, 0]
        except:
            pass
        return True

    #time_val - 0
    #total_time_val - 1
    #progress_val - 2
    #current_temp_nozzle - 3
    #target_temp_nozzle b- 4
    #current_temp_hotbed - 5
    #target_temp_hotbed - 6
    #speed - 7

    #Current temps
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetNozzoleTemp():
        return extracted_data[3]

    @unreal.ufunction(static=True, params=[], ret=int)
    def GetHotbedTemp():
        return extracted_data[5]

    #Target temps
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetTargetNozzoleTemp():
        return extracted_data[4]

    @unreal.ufunction(static=True, params=[], ret=int)
    def GetTargetHotbedTemp():
        return extracted_data[6]

    #Times
    @unreal.ufunction(static=True, params=[], ret=str)
    def GetTimeInString():
        seconds = extracted_data[0]
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(seconds))
        return formatted_time

    @unreal.ufunction(static=True, params=[], ret=float)
    def GetTimeValue():
        return extracted_data[0]

    #Progress
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetProgressValue():
        if extracted_data[0] == 0: #Check if time remaining is 0
            extracted_data[2] = 0   #Reset the progress
        return extracted_data[2]

    #Speed
    @unreal.ufunction(static=True, params=[], ret=int)
    def GetSpeedValue():
        if extracted_data[0] == 0: #Check if time remaining is 0
            extracted_data[7] = 0   #Reset the speed
        return extracted_data[7]






