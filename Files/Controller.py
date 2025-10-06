import time 
import pyautogui as pg

class Controller:
    def __init__(self):
        self.last = None

    def click(self, x, y):
        pg.click(x, y)

    def press(self, percept):
        if self.last == percept:
            return
        self.last = percept
        time.sleep(0.01)
        pg.press(percept)
        print(percept)
        return 

    def compute(self, percept):
        # print(f"Im controller, i received {percept}")
        if(percept[0] == "press"):
            self.press(percept[1])
        elif(percept[0] == "click"):
            self.click(percept[1],percept[2])
        elif(percept[0] == "pressDouble"):
            self.press(percept[1])
            time.sleep(0.03)
            self.press(percept[2])
