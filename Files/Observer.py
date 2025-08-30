import time
import mss
import numpy as np
import cv2 as cv

class Observer:
    def __init__(self):
        self.monitor = {"top": 0, "left": 0, "width": 0, "height": 0}
        self.dim = 0
        self.grid = []
        self.snk_l = 2

    def startGame(self):
        mss.mss().shot(output="startScreen.png")
        img = cv.imread("startScreen.png")

        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 250, 255, cv.THRESH_BINARY)
        contours, hierarchy  = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # Video que me ayudó con esto
        # https://www.youtube.com/watch?v=Wl11eloYVm8
        for contour in contours:
            epsilon = 0.02 * cv.arcLength(contour, True)               # presision of the aproximation of the shape
            approx = cv.approxPolyDP(contour, epsilon, True)           # True to indicate that the shape is closed

            if len(approx) == 3:
                x,y,w,h = cv.boundingRect(approx)
                x_mid = int(x+w/2)
                y_mid = int(y+h/2)
        
        return ([x_mid,y_mid])

    def getBoard(self):
        mss.mss().shot(output="Screen.png")
        img = cv.imread("Screen.png")

        # Video que me ayudo con las mascaras
        # https://www.youtube.com/watch?v=SJCu1d4xakQ&t=882s
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 160, 255, cv.THRESH_BINARY)
        contours, hierarchy  = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        img = cv.drawContours(im, contours, -1, (0,0,0), 0)                                # img = cv.drawContours(im, contours, -1, (150,255,75), 2)

        # cv.imwrite("mask.png", img)

        coords = max(contours, key=cv.contourArea)
        self.monitor["left"], self.monitor["top"] = coords[0][0]
        self.monitor["width"], self.monitor["height"] = coords[2][0] - coords[0][0]

        self.monitor = {k: int(v) for k, v in self.monitor.items()}

    def getGrid(self):
        img =  np.array(mss.mss().grab(self.monitor))

        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 180, 255, cv.THRESH_BINARY)
        contours, hierarchy  = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        img = cv.drawContours(im, contours, -1, (0,0,0), 0)                                 # img = cv.drawContours(im, contours, -1, (150,255,75), 2)
 
        # cv.imwrite("grid.png", img)

        self.dim = max(contours, key=cv.contourArea)[1][0][1]
        sqrs = self.monitor["height"] // self.dim
        self.grid = np.zeros((sqrs,sqrs))

    def getApple(self):
        img = np.array(mss.mss().grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        # Video que me ayudo
        # https://www.youtube.com/watch?v=cMJwqxskyek
        lower = np.array([ 0, 150, 100])          # (0-179, 0-255, 0-255)
        upper = np.array([10, 255, 255])          # (0-179, 0-255, 0-255)
        mask = cv.inRange(img_hsv, lower, upper)

        contours, hierarchy = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        if len(contours) != 0:
            for contour in contours:
                if cv.contourArea(contour) > 300:
                    x, y, w, h = cv.boundingRect(contour)
                    x_coor = int(x+w/2) // self.dim
                    y_coor = int(y+h/2) // self.dim
                    self.grid[y_coor][x_coor] = 1

    def getGame(self):
        img = np.array(mss.mss().grab(self.monitor))
        cv.imshow("Snake Bot", img)

time.sleep(1)

o = Observer()
# coords = o.startGame()
# print(*coords)

o.getBoard()
o.getGrid()

while "Game":
    o.getGame()

    if cv.waitKey(50) & 0xFF == ord("q"):
            cv.destroyAllWindows()
            break