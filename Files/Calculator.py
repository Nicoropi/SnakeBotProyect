import heapq
import numpy as np 
from enum import Enum
from collections import deque

class dirs(Enum):
    up = (-1, 0)
    down  = (1, 0)
    right = (0, 1)
    left = (0, -1)

# i liked this way, just for the beauty sjkdfdsj
# its the same as creating a dict with (position change) : "name of change"
# exmaple: (-1, 0) : up
inverseDirs = {v.value: v.name for v in dirs}

def flood_fill_space(grid, start):
    rows, cols = grid.shape
    visited = set()
    q = deque([start])
    visited.add(start)

    while q:
        r, c = q.popleft()
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and
                (nr, nc) not in visited and grid[nr, nc] not in (2, 9)):
                visited.add((nr, nc))
                q.append((nr, nc))
    return len(visited)


def find_tail(grid):
    body_positions = np.argwhere(grid == 2)
    if len(body_positions) == 0:
        return None
    # LOGIC: cell with one neighbor is the tail
    for r, c in body_positions:
        neighbors = 0
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < grid.shape[0] and 0 <= nc < grid.shape[1] and grid[nr, nc] == 2:
                neighbors += 1
        if neighbors == 1:
            return (r, c)
    # if not found
    return tuple(body_positions[-1]) 
    
# BFS is actually better for this approach, it produces "squared" paths
def reachable(grid, start, end):
    rows, cols = grid.shape
    q = deque([start])
    visited = {start}

    while q:
        r, c = q.popleft()
        if (r, c) == end:
            return True
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and
                (nr, nc) not in visited and grid[nr, nc] not in (2, 9)):
                visited.add((nr, nc))
                q.append((nr, nc))
    return False

def follow_tail_move(grid, head):
    directions = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1)
    }

    tail = find_tail(grid)
    if tail is None:
        return None

    best_move = None
    best_score = -float("inf")

    for name, (dr, dc) in directions.items():
        new_r, new_c = head[0] + dr, head[1] + dc
        if grid[new_r, new_c] in (2, 9):
            continue

        grid_copy = np.copy(grid)
        grid_copy[new_r, new_c] = 2
        grid_copy[tail] = 0  # tail moves away next frame

        # measure open space
        space = flood_fill_space(grid_copy, (new_r, new_c))
        dist_tail = abs(new_r - tail[0]) + abs(new_c - tail[1])
        reachable_tail = reachable(grid_copy, (new_r, new_c), tail)

        # prefer moves that keep space large and tail reachable
        score = space - dist_tail * 3
        if reachable_tail:
            score += 100  # strong bonus for keeping tail path open

        if score > best_score:
            best_score = score
            best_move = name

    return best_move


def greedy_safe_move(grid, head, apple):
    directions = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1)
    }

    tail = find_tail(grid)
    if tail is None:
        tail = head

    best_move = None
    best_score = -float("inf")

    for name, (dr, dc) in directions.items():
        new_r, new_c = head[0] + dr, head[1] + dc
        if grid[new_r, new_c] in (2, 9):
            continue

        grid_copy = np.copy(grid)
        grid_copy[new_r, new_c] = 2
        grid_copy[tail] = 0

        # compute metrics
        reachable_tail = reachable(grid_copy, (new_r, new_c), tail)
        space = flood_fill_space(grid_copy, (new_r, new_c))
        dist_apple = abs(new_r - apple[0]) + abs(new_c - apple[1])

        # scoring logic: prioritize survival & space first, apple proximity second
        score = space - dist_apple * 2
        if reachable_tail:
            score += 200  # strong safety bonus

        if score > best_score:
            best_score = score
            best_move = name

    # if no safe move, follow tail
    if best_move is None:
        return follow_tail_move(grid, head)

    return best_move

class Calculator():
    def __init__(self):
        self.last = None

    def compute(self, percept):
        if percept is None:
            print("SOMETHING BAD HAPPENED")
            return

        move = greedy_safe_move(percept[0], percept[1], percept[2])

        if move is None:
            move = follow_tail_move(percept[0], percept[1])

        if move is not None:
            self.last = move
            return ["press", move]
        else:
            print("No movements")
            return ["press", self.last]
