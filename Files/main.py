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


    GOOGLE_SNAKE_FPS = 60  # Estimate this by observation
    FRAME_TIME = 1.0 / GOOGLE_SNAKE_FPS
    last_frame_time = time.time()
    while True:
        # returns new move for the current state "press", {"up", "down", "left", "right"}
        if gameState[2] is not None:
            nextMove = calc.compute(gameState)
            # executes the move
            contr.compute(nextMove)
       # Wait until next frame boundary
        current_time = time.time()
        time_since_last = current_time - last_frame_time
        
        if time_since_last < FRAME_TIME:
            time.sleep(FRAME_TIME - time_since_last)
        gameState = obs.compute(nextMove[1])
        if not np.array_equal(lastState, gameState[0]):
            # print(gameState[0])
            lastState = gameState[0].copy()

if __name__ == "__main__":
    main()
