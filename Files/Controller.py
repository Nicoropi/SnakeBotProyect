import pyautogui as pg
from enum import Enum

# no se si realmente es necesario esto... pero por si algo aquí está

class dirs(Enum):
    u = 'up'
    d  = 'down'
    r = 'right'
    l = 'left'

class Controller():
    def __init__(self):
        self.last = None

    def compute(self, percept):
        if self.last == percept:
            return
        
        self.last = percept
        pg.press(percept)
        return
    
c = Controller()
c.compute(dirs.LEFT)