from collections import deque
import time
import mss
import numpy as np
import cv2 as cv
import pyautogui as pg

class Observer:
    def __init__(self):
        self.monitor = {"top": 0, "left": 0, "width": 0, "height": 0}
        self.dim = 0
        self.grid = []
        self.snake = deque()
        self.sct = mss.mss()

    def startGame(self):
        img = np.array(self.sct.grab(self.sct.monitors[1]))

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
        img = np.array(self.sct.grab(self.sct.monitors[1]))

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
        img =  np.array(self.sct.grab(self.monitor))

        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 180, 255, cv.THRESH_BINARY)
        contours, hierarchy  = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        img = cv.drawContours(im, contours, -1, (0,0,0), 0)                                 # img = cv.drawContours(im, contours, -1, (150,255,75), 2)
 
        # cv.imwrite("grid.png", img)

        self.dim = max(contours, key=cv.contourArea)[1][0][1] + 1
        y_sqrs = (self.monitor["height"] // (self.dim - 1)) + 2
        x_sqrs = (self.monitor["width"] // (self.dim - 1)) + 2
        self.grid = np.zeros((y_sqrs,x_sqrs))

        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if j == 0 or j == len(self.grid[0])-1 or i == 0 or i == len(self.grid)-1:
                    self.grid[i][j] = 9

    def getApple(self):
        img = np.array(self.sct.grab(self.monitor))
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
                    self.grid[y_coor+1][x_coor+1] = 1
                    return True
        
        return False

    def getSnake(self):
        # Aqui me complique re duro, asi que capaz esto se puede mejorar un monton

        # Esta parte reconoce solo la cabeza y la guarda en la matriz
        img = np.array(self.sct.grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        lower = np.array([110, 150, 240])          # (0-179, 0-255, 0-255)
        upper = np.array([120, 255, 255])          # (0-179, 0-255, 0-255)
        mask = cv.inRange(img_hsv, lower, upper)

        contours, hierarchy = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        if len(contours) != 0:
            for contour in contours:
                if cv.contourArea(contour) > 300:
                    x, y, w, h = cv.boundingRect(contour)
                    x_coor = (int(x+w/2) // self.dim) + 1
                    y_coor = (int(y+h/2) // self.dim) + 1
                    self.grid[y_coor][x_coor] = 2

        # todo esto es para reconocer el resto de la serpiente y guardarla en la matriz y en la queue que representa la serpiente
        temp_list = [[int(y_coor), int(x_coor)]]
        q = deque()
        q.append([y_coor, x_coor]) 

        lower = np.array([110, 150, 150])          # (0-179, 0-255, 0-255)
        upper = np.array([120, 255, 255])          # (0-179, 0-255, 0-255)
        mask = cv.inRange(img_hsv, lower, upper)

        area = self.dim * self.dim
        while q:
            cy,cx = q.pop()                        # Grid coordinates
            vx = cx-1; vy = cy-1                   # Image coordinates

            if self.grid[cy][cx-1] == 0:
                sqr = mask[(vy)*self.dim:(vy+1)*self.dim, (vx-1)*self.dim:(vx)*self.dim]
                blue_pixels = cv.countNonZero(sqr)
                ratio = blue_pixels / area
                if ratio > 0.25:
                    self.grid[cy][cx-1] = 2
                    q.append([cy, cx-1])
                    temp_list.append([int(cy), int(cx-1)])

        for element in (temp_list[::-1]):
            self.snake.append(element)

    def getGame(self):
        img = np.array(self.sct.grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        lower = np.array([110, 150, 150])          # (0-179, 0-255, 0-255)
        upper = np.array([120, 255, 255])          # (0-179, 0-255, 0-255)
        mask = cv.inRange(img_hsv, lower, upper)

        q = deque()
        q.append(self.snake[-1]) 
        area = self.dim * self.dim
        
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        while q:
            cy,cx = q.pop()                        # Grid coordinates
            vx = cx-1; vy = cy-1                   # Image coordinates

            for ny,nx in directions:
                if self.grid[cy+ny][cx+nx] == 0 or self.grid[cy+ny][cx+nx]==1:
                    sqr = mask[(vy+ny)*self.dim:(vy+ny+1)*self.dim, (vx+nx)*self.dim:(vx+nx+1)*self.dim]
                    blue_pixels = cv.countNonZero(sqr)
                    ratio = blue_pixels / area

                    if ratio > 0.3:
                        if self.grid[cy+ny][cx+nx]==1:
                            self.snake.append([cy+ny, cx+nx])
                            self.grid[cy+ny][cx+nx] = 2
                            q.append([cy+ny, cx+nx])
                            res = self.getApple()
                            while not res:
                                res = self.getApple()
                        else:
                            self.snake.append([cy+ny, cx+nx])
                            self.grid[cy+ny][cx+nx] = 2
                            q.append([cy+ny, cx+nx])
                            dy,dx = self.snake.popleft()
                            self.grid[dy,dx] = 0
                            
                        print(self.grid)

    def compute(self, percept = None):
        if percept == None:
            self.getGame()

        if percept == "init":
            time.sleep(0.5)
            pg.click(self.startGame())
            
            time.sleep(0.5)
            o.getBoard()
            o.getGrid()
            o.getApple()
            o.getSnake()

            print(self.grid)


o = Observer()
o.compute('init')

while True:
    o.compute()