from collections import deque
# from controller import Controller
import time
import mss
import numpy as np
import cv2 as cv

class Observer:
    def __init__(self):
        self.monitor = {"top": 0, "left": 0, "width": 0, "height": 0}
        self.dim = 0
        self.grid = []
        self.snake = deque()
        self.sct = mss.mss()
        self.head = None
        self.apple = None
        self.lastHead = None
        self.tail = None

    def startGame(self):
        img = np.array(self.sct.grab(self.sct.monitors[0]))

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
        img = np.array(self.sct.grab(self.sct.monitors[0]))

        # Video que me ayudo con las mascaras
        # https://www.youtube.com/watch?v=SJCu1d4xakQ&t=882s
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 160, 255, cv.THRESH_BINARY)
        contours, hierarchy  = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        img = cv.drawContours(im, contours, -1, (0,0,0), 0)                                # img = cv.drawContours(im, contours, -1, (150,255,75), 2)

        # cv.imwrite("mask.png", img)

        coords = max(contours, key=cv.contourArea)
        x, y, w, h = cv.boundingRect(coords)

        self.monitor["left"] = x
        self.monitor["top"] = y
        self.monitor["width"] = w
        self.monitor["height"] = h
        # self.monitor["left"], self.monitor["top"] = coords[0][0]
        # self.monitor["width"], self.monitor["height"] = coords[2][0] - coords[0][0]

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

        self.grid[0, :] = 9
        self.grid[:,0] = 9
        self.grid[-1,:] = 9
        self.grid[:,-1] = 9

    def getApple(self):
        img = np.array(self.sct.grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        # Downscaling
        scale = 0.5
        small = cv.resize(img_hsv, (0, 0), fx=scale, fy=scale)

        lower = np.array([0,  150, 150])   # ejemplo: verde
        upper = np.array([10, 255, 255])
        mask = cv.inRange(small, lower, upper)

        ys, xs = np.where(mask > 0)
        if len(xs) == 0 or len(ys) == 0:
            return None

        x_mid = int(((xs.min() + xs.max()) // 2) / scale)
        y_mid = int(((ys.min() + ys.max()) // 2) / scale)

        # Coordenada en grid
        x_coor = (x_mid // self.dim) + 1
        y_coor = (y_mid // self.dim) + 1
        self.apple = (y_coor, x_coor)
        self.grid[y_coor][x_coor] = 1

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
                if ratio > 0.15:
                    self.grid[cy][cx-1] = 2
                    q.append([cy, cx-1])
                    temp_list.append([int(cy), int(cx-1)])

        for element in (temp_list[::-1]):
            self.snake.append(element)
        # print(self.snake)
        self.head = (temp_list[0][0], temp_list[0][1])

    def cell_has_snake(self, mask, y, x, threshold=0.35):
        y0, y1 = (y-1)*(self.dim+1), y*(self.dim+1) 
        x0, x1 = (x-1)*(self.dim+1), x*(self.dim+1) 
        sqr = mask[y0:y1, x0:x1] 
        ratio = cv.countNonZero(sqr) / (self.dim * self.dim) 
        return ratio > threshold 
    
    def getHead(self, mask, last_dir, head): 
        ys, xs = np.where(mask > 0) 
        if len(xs) == 0 or len(ys) == 0: 
            return head # Pasar todos los píxeles detectados a coordenadas de grid 
        
        points = {(y // self.dim + 1, x // self.dim + 1) for y, x in zip(ys, xs)} 
        
        expected = { 
            "up": (head[0] - 1, head[1]), 
            "down": (head[0] + 1, head[1]), 
            "left": (head[0], head[1] - 1), 
            "right": (head[0], head[1] + 1),
        }[last_dir] 
        
        if expected in points and self.cell_has_snake(mask, *expected): 
            return expected 
        
        if last_dir == "up":
            min_y = min(p[0] for p in points) 
            candidates = [p for p in points if p[0] == min_y] 
            return min(candidates, key=lambda p: abs(p[1] - head[1])) 
        
        elif last_dir == "down": 
            max_y = max(p[0] for p in points) 
            candidates = [p for p in points if p[0] == max_y] 
            return min(candidates, key=lambda p: abs(p[1] - head[1])) 
        
        elif last_dir == "left": 
            min_x = min(p[1] for p in points) 
            candidates = [p for p in points if p[1] == min_x] 
            return min(candidates, key=lambda p: abs(p[0] - head[0])) 
        
        elif last_dir == "right": 
            max_x = max(p[1] for p in points) 
            candidates = [p for p in points if p[1] == max_x] 
            return min(candidates, key=lambda p: abs(p[0] - head[0])) 
        
        return head 
    
    def getGame(self, dir): 
        img = np.array(self.sct.grab(self.monitor)) 
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV) 
        
        lower = np.array([110, 150, 150]) # (0-179, 0-255, 0-255) 
        upper = np.array([120, 255, 255]) # (0-179, 0-255, 0-255) 
        mask = cv.inRange(img_hsv, lower, upper) 
        
        # Calcular coordenada en grid directamente 
        # ys, xs = np.where(mask > 0) 
        # points = {(y // self.dim + 1, x // self.dim + 1) for y, x in zip(ys, xs)} 
        
        new_head = self.getHead(mask, dir, self.head) 
        # print(new_head) 
        
        # --- híbrido --- 
        dy = abs(new_head[0] - self.head[0]) 
        dx = abs(new_head[1] - self.head[1]) 
        
        if dy + dx == 0: 
            if self.apple and new_head == self.apple:
                self.apple = None 
                
            return 
        
        elif dy + dx == 1: 
            # Caso normal → incremental (se movió una celda) 
            self.snake.append(new_head) 
            self.grid[new_head] = 2 
            self.head = new_head 
            
            if self.apple and new_head == self.apple: 
                self.apple = None 
            else: 
                tail_y, tail_x = self.snake.popleft() 
                self.grid[tail_y, tail_x] = 0 
                
        else: 
            # Se saltó más de una celda → opcional: reconstrucción completa
            # (si no quieres reconstrucción, simplemente "return") 
            # self.grid[self.grid == 2] = 0 
            # self.snake.clear() 
            # self.snake.append(new_head) 
            # self.grid[new_head] = 2 
            # self.head = new_head 
            return

    def compute(self, percept = None):
        # print(f"Im observer, i received {percept}")
        if percept in ["up", "down", "right", "left"]:

            self.getGame(percept)
            if not self.apple:
                self.getApple()
            
            # print(self.grid)
            return [self.grid, self.head, self.apple, self.tail]

        elif percept == "init":
            time.sleep(0.3)
            return self.startGame()

        elif percept == "define":
            time.sleep(0.3)
            self.getBoard()
            self.getGrid()
            self.getApple()
            self.getSnake()
            # print(self.grid, self.head, self.apple)
            return [self.grid, self.head, self.apple]