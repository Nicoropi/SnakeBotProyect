import heapq
import numpy as np 
from enum import Enum

class dirs(Enum):
    up = (-1, 0)
    down  = (1, 0)
    right = (0, 1)
    left = (0, -1)

# i liked this way, just for the beauty sjkdfdsj
# its the same as creating a dict with (position change) : "name of change"
# exmaple: (-1, 0) : up
inverseDirs = {v.value: v.name for v in dirs}

class Node():
    def __init__(self, parent = None, position = None):
        self.parent = parent 
        self.position = position 
        # define attributes required for f(x) = g(x) + h(x)
        self.g = 0
        self.h = 0
        self.f = 0 

    # define method for comparing nodes 
    def __eq__(self, other):
        return self.position == other.position 

    # define method for < operator
    def __lt__(self, other):
        return self.f < other.f

def astar(grid, start, end):
    startNode = Node(None, start)
    endNode = Node(None, end)

    openList = []
    closedSet = set()

    openList.append(startNode)
    heapq.heappush(openList, startNode)

    while openList:
        currentNode = heapq.heappop(openList)
        closedSet.add(tuple(currentNode.position))

        # backtracking if node was found
        if currentNode == endNode:
            path = []
            current = currentNode 
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]

        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        for direction in directions:
            row, col = currentNode.position 
            newRow, newCol = row + direction[0], col + direction[1]
            # avoid snake's body and walls
            if grid[newRow, newCol] == 2 or grid[newRow, newCol] == 9 :
                continue
            newPosition = (newRow, newCol)
            if newPosition in closedSet:
                continue

            child = Node(currentNode, newPosition)
            child.g = currentNode.g + 1
            child.h = abs(newRow - endNode.position[0]) + abs(newCol - endNode.position[1])
            child.f = child.g + child.h 

            skip = False 
            for openNode in openList:
                if child == openNode and child.g >= openNode.g:
                    skip = True 
                    break 
            if skip:
                continue 
            heapq.heappush(openList, child)
    return None

def genGrid(rows = 17, cols = 19):
    grid = np.zeros((rows, cols))
    grid[0, :] = 9
    grid[:,0] = 9
    grid[-1,:] = 9
    grid[:,-1] = 9
    return grid 

def pathChanges(path):
    directions = []
    for i in range(len(path) - 1):
        change = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        changeName = inverseDirs.get(change,"ERROR")
        directions.append(changeName)
    return directions

class Calculator():
    def __init__(self):
        self.apple = None
        self.last = None

    def compute(self, percept):
        # print(f"Im calculator, i received {percept}")
        if percept is not None:
            path = astar(percept[0], percept[1],percept[2])
            #return ["press", pathChanges(path)[0]]

            res = pathChanges(path)
            if len(res) > 0:
                self.last = res[0]
                return ["press", res[0]]
            
            return ["press", self.last]
            
            
        else:
            print("SOMETHING BAD HAPPENED")
            return 
