from collections import deque
import time
import mss
import numpy as np
import cv2 as cv

class Observer:
    def __init__(self):
        self.monitor = {"top": 0, "left": 0, "width": 0, "height": 0}
        self.dim = 0
        self.grid = []
        self.gridCoords = []
        self.snake = deque()
        self.sct = mss.mss()
        self.head = None
        self.apple = None
        self.length = 4

    def startGame(self):
        img = np.array(self.sct.grab(self.sct.monitors[0]))
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 250, 255, cv.THRESH_BINARY)
        contours, hierarchy = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            epsilon = 0.02 * cv.arcLength(contour, True)
            approx = cv.approxPolyDP(contour, epsilon, True)

            if len(approx) == 3:
                x, y, w, h = cv.boundingRect(approx)
                x_mid = int(x + w / 2)
                y_mid = int(y + h / 2)
                return [x_mid, y_mid]

    def getBoard(self):
        img = np.array(self.sct.grab(self.sct.monitors[0]))
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 160, 255, cv.THRESH_BINARY)
        contours, hierarchy = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        coords = max(contours, key=cv.contourArea)
        x, y, w, h = cv.boundingRect(coords)

        self.monitor["left"] = int(x)
        self.monitor["top"] = int(y)
        self.monitor["width"] = int(w)
        self.monitor["height"] = int(h)

    def getGrid(self):
        img = np.array(self.sct.grab(self.monitor))
        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        ret, im = cv.threshold(img_gray, 180, 255, cv.THRESH_BINARY)
        contours, hierarchy = cv.findContours(im, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        self.dim = max(contours, key=cv.contourArea)[1][0][1] + 1
        y_sqrs = (self.monitor["height"] // (self.dim - 1)) + 2
        x_sqrs = (self.monitor["width"] // (self.dim - 1)) + 2
        self.grid = np.zeros((y_sqrs, x_sqrs))

        self.grid[0, :] = 9
        self.grid[:, 0] = 9
        self.grid[-1, :] = 9
        self.grid[:, -1] = 9

        self.gridCoords = np.full((y_sqrs, x_sqrs, 2), -1, dtype=int)
        temp = self.dim // 2

        for i in range(1, y_sqrs - 1):
            for j in range(1, x_sqrs - 1):
                cy = ((i - 1) * self.dim) + temp
                cx = ((j - 1) * self.dim) + temp
                self.gridCoords[i, j] = [cy, cx]

    def getApple(self):
        img = np.array(self.sct.grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        scale = 0.5
        small = cv.resize(img_hsv, (0, 0), fx=scale, fy=scale)

        lower = np.array([0, 150, 150])
        upper = np.array([10, 255, 255])
        mask = cv.inRange(small, lower, upper)

        ys, xs = np.where(mask > 0)
        if len(xs) == 0 or len(ys) == 0:
            return None

        x_mid = int(((xs.min() + xs.max()) // 2) / scale)
        y_mid = int(((ys.min() + ys.max()) // 2) / scale)

        x_coor = (x_mid // self.dim) + 1
        y_coor = (y_mid // self.dim) + 1
        self.apple = (y_coor, x_coor)
        self.grid[y_coor][x_coor] = 1

    def getSnake(self):
        img = np.array(self.sct.grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        lower = np.array([110, 150, 240])
        upper = np.array([120, 255, 255])
        mask = cv.inRange(img_hsv, lower, upper)

        contours, hierarchy = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        if len(contours) != 0:
            for contour in contours:
                if cv.contourArea(contour) > 300:
                    x, y, w, h = cv.boundingRect(contour)
                    x_coor = (int(x + w / 2) // self.dim) + 1
                    y_coor = (int(y + h / 2) // self.dim) + 1
                    self.grid[y_coor][x_coor] = 2

        temp_list = [[int(y_coor), int(x_coor)]]
        q = deque()
        q.append([y_coor, x_coor])

        lower = np.array([110, 150, 150])
        upper = np.array([120, 255, 255])
        mask = cv.inRange(img_hsv, lower, upper)

        area = self.dim * self.dim
        while q:
            cy, cx = q.pop()
            vx = cx - 1
            vy = cy - 1

            if self.grid[cy][cx - 1] == 0:
                sqr = mask[(vy) * self.dim:(vy + 1) * self.dim, (vx - 1) * self.dim:(vx) * self.dim]
                blue_pixels = cv.countNonZero(sqr)
                ratio = blue_pixels / area
                if ratio > 0.15:
                    self.grid[cy][cx - 1] = 2
                    q.append([cy, cx - 1])
                    temp_list.append([int(cy), int(cx - 1)])

        for element in temp_list[::-1]:
            self.snake.append(element)
        self.head = (temp_list[0][0], temp_list[0][1])

    def getHead(self, mask, last_dir, head):
        points = set()

        y_sqrs, x_sqrs = self.gridCoords.shape[:2]
        tile_size = self.dim
        threshold_body = int(tile_size * tile_size * 0.15)

        for i in range(1, y_sqrs - 1):
            for j in range(1, x_sqrs - 1):
                y0 = (i - 1) * tile_size
                y1 = i * tile_size
                x0 = (j - 1) * tile_size
                x1 = j * tile_size

                if y1 <= mask.shape[0] and x1 <= mask.shape[1]:
                    body_pixels = cv.countNonZero(mask[y0:y1, x0:x1])
                    if body_pixels > threshold_body:
                        points.add((i, j))

        expected = {
            "up": (head[0] - 1, head[1]),
            "down": (head[0] + 1, head[1]),
            "left": (head[0], head[1] - 1),
            "right": (head[0], head[1] + 1),
        }[last_dir]

        if expected in points:
            return expected

        if points:
            frontier = [p for p in points if abs(p[0] - head[0]) + abs(p[1] - head[1]) <= 2]

            if frontier:
                if last_dir == "up":
                    min_y = min(p[0] for p in frontier)
                    candidates = [p for p in frontier if p[0] == min_y]
                    return min(candidates, key=lambda p: abs(p[1] - head[1]))

                elif last_dir == "down":
                    max_y = max(p[0] for p in frontier)
                    candidates = [p for p in frontier if p[0] == max_y]
                    return min(candidates, key=lambda p: abs(p[1] - head[1]))

                elif last_dir == "left":
                    min_x = min(p[1] for p in frontier)
                    candidates = [p for p in frontier if p[1] == min_x]
                    return min(candidates, key=lambda p: abs(p[0] - head[0]))

                elif last_dir == "right":
                    max_x = max(p[1] for p in frontier)
                    candidates = [p for p in frontier if p[1] == max_x]
                    return min(candidates, key=lambda p: abs(p[0] - head[0]))

        return head


    def getGame(self, dir):
        img = np.array(self.sct.grab(self.monitor))
        img_hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        lower_body = np.array([110, 150, 150])
        upper_body = np.array([120, 255, 255])
        mask = cv.inRange(img_hsv, lower_body, upper_body)

        kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

        new_head = self.getHead(mask, dir, self.head)

        dy = abs(new_head[0] - self.head[0])
        dx = abs(new_head[1] - self.head[1])
        if dy + dx == 0:
            if self.apple and new_head == self.apple:
                self.length +=1
                self.apple = None
            return

        elif dy + dx == 1:
            self.snake.append(new_head)
            self.grid[new_head] = 2
            self.head = new_head

            if self.apple and new_head == self.apple:
                self.length +=1
                self.apple = None
            else:
                tail_y, tail_x = self.snake.popleft()
                self.grid[tail_y, tail_x] = 0
        else:
            return

    def compute(self, percept=None):
        if percept in ["up", "down", "right", "left"]:
            self.getGame(percept)
            if not self.apple:
                self.getApple()
            return [self.grid, self.head, self.apple]

        elif percept == "init":
            time.sleep(0.3)
            return self.startGame()

        elif percept == "define":
            time.sleep(0.3)
            self.getBoard()
            self.getGrid()
            self.getApple()
            self.getSnake()
            return [self.grid, self.head, self.apple]
