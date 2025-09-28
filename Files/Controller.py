from enum import Enum
import time 
import pyautogui as pg

class dirs(Enum):
    u = 'up'
    d  = 'down'
    r = 'right'
    l = 'left'

class Controller:
    def __init__(self):
        self.last = None

    def click(self, x, y):
        pg.click(x, y)

    def press(self, percept):
        if self.last == percept:
            return
        self.last = percept
        pg.press(percept)
        print(percept)
        return 


    def compute(self, percept):
        # print(f"Im controller, i received {percept}")
        if(percept[0] == "press"):
            self.press(percept[1])
        elif(percept[0] == "click"):
            self.click(percept[1],percept[2])
