import pandas as pd

def read_file():
    df = pd.read_csv('C:\\Users\\Alien\\Desktop\\HuusStuff\\DeconstructingGcode\\LastestCode\\WriteData\\DeconstructedGcode_2.txt')
    x = []
    x = df["E"].to_list()
    print(x)
    print(len(x))
    

read_file()