import unreal
import os
from threading import Thread

def executeTerminal(command):
    os.system(command)

@unreal.uclass()
class PrinterFunctions(unreal.BlueprintFunctionLibrary):

    @unreal.ufunction(static = True, params = [str], ret = bool)
    def PrintFile(FilePath):
        Thread(target=executeTerminal, args=(f"python3 C:\\Users\\Alien\\ankermake-m5-protocol\\ankerctl.py pppp print-file {FilePath}", )).start()
        return True
    




