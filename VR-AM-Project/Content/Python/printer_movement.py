from threading import Thread
import pandas as pd
import unreal

x = []
y = []
time = []

def reading_data(file_name):
    df = pd.read_csv('C:\\Users\\Alien\\Desktop\\HuusStuff\\DeconstructingGcode\\LastestCode\\WriteData\\DeconstructedGcode_2.txt')
    global x, y, time
    x = df["x [mm]"].tolist()
    y = df["y [mm]"].tolist()
    time = df["Time [s]"].tolist()


@unreal.uclass()
class GetMovementData(unreal.BlueprintFunctionLibrary):
    @unreal.ufunction(static = True, params =[], ret = bool)
    def GenerateData():
        reading_data("None")
        
    @unreal.ufunction(static = True, params = [], ret = unreal.Array(float))
    def GetXPositions():
        global x
        new_x = [round(num / 10, 2) for num in x]
        return new_x
    
    @unreal.ufunction(static = True, params = [], ret = unreal.Array(float))
    def GetYPositions():
        global y
        new_y = [round(num / 10, 2) for num in y]
        return new_y
    
    @unreal.ufunction(static = True, params = [], ret = unreal.Array(float))
    def GetTime():
        global time
        new_time = [round(num, 2) for num in time]
        return new_time

