# Environment
from Controller import Controller
from Observer import Observer 
from Calculator import Calculator
import numpy as np
import time

def main():
    # Create agents for controlling keyboard, observing screen and calculating routes
    contr = Controller()
    obs = Observer()
    calc = Calculator()
    # Get start button from screen
    position = obs.compute("init")
    # Press start button
    contr.compute(["click", position[0], position[1]])
    # Get grid and make a map of the game
    gameState = obs.compute("define")
    # DEBUG GRID CHANGES OVER TIME
    lastState = gameState[0].copy()

    while True:
        # returns new move for the current state "press", {"up", "down", "left", "right"}
        if gameState[2] is not None:
            # print(gameState[0])
            nextMove = calc.compute(gameState)
            # executes the move
            contr.compute(nextMove)
       # Wait until next frame boundary

        gameState = obs.compute(nextMove[1])
        if not np.array_equal(lastState, gameState[0]):
            print(gameState[0])
            lastState = gameState[0].copy()

if __name__ == "__main__":
    main()
