# Environment
from controller import Controller
from observer import Observer 
from calculator import Calculator
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

    while True:
        # returns new move for the current state "press", {"up", "down", "left", "right"}
        if gameState[2] is not None:
            nextMove = calc.compute(gameState)

            # executes the move
            contr.compute(nextMove)

        gameState = obs.compute(nextMove[1])
        #print(gameState[1:])

if __name__ == "__main__":
    main()
