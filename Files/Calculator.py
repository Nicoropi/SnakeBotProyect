import heapq
import numpy as np 
from enum import Enum
from collections import deque

class dirs(Enum):
    up = (-1, 0)
    down  = (1, 0)
    right = (0, 1)
    left = (0, -1)

inverseDirs = {v.value: v.name for v in dirs}

class Node():
    def __init__(self, parent = None, position = None):
        self.parent = parent 
        self.position = position 

        self.g = 0
        self.h = 0
        self.f = 0 

    def __eq__(self, other):
        return self.position == other.position 

    def __lt__(self, other):
        return self.f < other.f

def calculate_danger_map(grid, snake_body):
    danger_map = np.zeros_like(grid, dtype=float)

    for body_part in snake_body:
        x, y = body_part
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < grid.shape[0] and 0 <= new_y < grid.shape[1]:
                    danger_map[new_x, new_y] += 0.5

    return danger_map

def survival_mode(grid, start, snake_body):
    """
    Implementa el modo supervivencia cuando la serpiente está encerrada.
    Intenta encontrar el camino que maximiza el espacio disponible.
    """
    space_info = analyze_space(grid, start, snake_body)

    if space_info['is_enclosed']:

        if space_info['nearest_exit']:
            return [start, space_info['nearest_exit']]

        if len(space_info['longest_path']) > 1:
            return space_info['longest_path'][:2]

    elif space_info['danger_level'] > 0:
        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        best_space = 0
        best_move = None

        for direction in directions:
            next_pos = (start[0] + direction[0], start[1] + direction[1])
            if (0 <= next_pos[0] < grid.shape[0] and 
                0 <= next_pos[1] < grid.shape[1] and 
                grid[next_pos] != 9 and 
                grid[next_pos] != 2):
                next_space = analyze_space(grid, next_pos, snake_body)
                if next_space['available_space'] > best_space:
                    best_space = next_space['available_space']
                    best_move = next_pos

        if best_move:
            return [start, best_move]

    return None

def evaluate_move(grid, pos, direction, snake_body, snake_length, target=None, last_move=None):
    """
    Evalúa la seguridad y calidad de un movimiento en una dirección específica.
    Retorna un score y información sobre el movimiento.
    """
    new_pos = (pos[0] + direction[0], pos[1] + direction[1])

    if not (0 <= new_pos[0] < grid.shape[0] and 
            0 <= new_pos[1] < grid.shape[1] and 
            grid[new_pos] != 9 and 
            grid[new_pos] != 2):
        return {'score': -float('inf'), 'position': new_pos, 'safe': False}

    if last_move is not None:
        last_dir = (last_move[1][0] - last_move[0][0], 
                   last_move[1][1] - last_move[0][1])
        if direction == last_dir:
            return {'score': -float('inf'), 'position': new_pos, 'safe': False}

    flood_result = flood_fill(grid, new_pos, snake_body, max_depth=snake_length * 2)

    score = 0
    safe = True

    space_weight = 2.0
    connectivity_weight = 1.5
    target_weight = 1.0

    available_space = len(flood_result['accessible_cells'])
    if available_space < snake_length:
        safe = False
        score -= 1000
    else:
        score += (available_space / snake_length) * space_weight

    open_paths = len(flood_result['open_paths'])
    score += (open_paths * connectivity_weight)

    dead_ends = len(flood_result['dead_ends'])
    score -= (dead_ends * 0.5)

    if target is not None:
        distance = abs(new_pos[0] - target[0]) + abs(new_pos[1] - target[1])
        score += (1.0 / (distance + 1)) * target_weight

    return {
        'score': score,
        'position': new_pos,
        'safe': safe,
        'space': available_space,
        'open_paths': open_paths,
        'dead_ends': dead_ends
    }

def find_safe_alternative(grid, start, snake_body, snake_length, target=None, last_move=None):
    """
    Busca una dirección segura cuando el camino principal falla.
    Evalúa múltiples factores para encontrar el mejor movimiento posible.
    """
    directions = [(0,1), (0,-1), (1,0), (-1,0)]
    moves_evaluated = []

    for direction in directions:
        eval_result = evaluate_move(grid, start, direction, snake_body, 
                                  snake_length, target, last_move)
        if eval_result['safe']:
            moves_evaluated.append(eval_result)

    if moves_evaluated:

        best_move = max(moves_evaluated, key=lambda x: x['score'])
        return [start, best_move['position']]

    survival_path = survival_mode(grid, start, snake_body)
    if survival_path:
        return survival_path

    for direction in directions:
        new_pos = (start[0] + direction[0], start[1] + direction[1])
        if (0 <= new_pos[0] < grid.shape[0] and 
            0 <= new_pos[1] < grid.shape[1] and 
            grid[new_pos] != 9 and 
            grid[new_pos] != 2):
            return [start, new_pos]

    return None

def astar(grid, start, end, snake_body=None, calculator=None):
    try:

        if not isinstance(grid, np.ndarray):
            raise PathFindingError("Grid must be a numpy array")
        if not all(isinstance(pos, (tuple, list)) and len(pos) == 2 for pos in [start, end]):
            raise PathFindingError("Start and end positions must be 2D coordinates")

        if snake_body is not None:
            space_info = analyze_space(grid, start, snake_body)
            if space_info['is_enclosed'] or space_info['danger_level'] > len(snake_body) / 3:
                survival_path = survival_mode(grid, start, snake_body)
                if survival_path:
                    return survival_path

        if calculator is not None:
            cache_key = (tuple(start), tuple(end), tuple(map(tuple, snake_body)) if snake_body is not None else None)
            if cache_key in calculator.path_cache:
                calculator.last_valid_path = calculator.path_cache[cache_key]
                return calculator.last_valid_path
    except Exception as e:
        if calculator is not None:
            calculator.recovery_attempts += 1
            if calculator.recovery_attempts <= calculator.max_recovery_attempts:
                if calculator.last_valid_path:
                    return calculator.last_valid_path
                elif snake_body is not None:
                    return find_safe_alternative(grid, start, snake_body, len(snake_body))
        raise PathFindingError(f"Error in pathfinding: {str(e)}")

    startNode = Node(None, start)
    endNode = Node(None, end)

    openList = []
    closedSet = set()

    danger_map = calculate_danger_map(grid, snake_body) if snake_body is not None else np.zeros_like(grid)

    openList.append(startNode)
    heapq.heappush(openList, startNode)

    while openList:
        currentNode = heapq.heappop(openList)
        closedSet.add(tuple(currentNode.position))

        if currentNode == endNode:
            path = []
            current = currentNode 
            while current is not None:
                path.append(current.position)
                current = current.parent
            final_path = path[::-1]

            if calculator is not None:
                cache_key = (tuple(start), tuple(end), tuple(map(tuple, snake_body)) if snake_body is not None else None)
                calculator.path_cache[cache_key] = final_path

                if len(calculator.path_cache) > calculator.cache_limit:
                    calculator.path_cache.pop(next(iter(calculator.path_cache)))
            return final_path

        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        for direction in directions:
            row, col = currentNode.position 
            newRow, newCol = row + direction[0], col + direction[1]

            if grid[newRow, newCol] == 2 or grid[newRow, newCol] == 9 :
                continue
            newPosition = (newRow, newCol)
            if newPosition in closedSet:
                continue

            child = Node(currentNode, newPosition)

            child.g = currentNode.g + 1

            base_distance = abs(newRow - endNode.position[0]) + abs(newCol - endNode.position[1])
            danger_cost = danger_map[newRow, newCol] * 2  

            child.h = base_distance + danger_cost
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

def flood_fill(grid, start_pos, snake_body=None, max_depth=None):

    if snake_body is None:
        snake_body = set()
    else:
        snake_body = set(snake_body)

    result = {
        'accessible_cells': set(),
        'dead_ends': set(),
        'open_paths': set(),
        'space_score': 0,
        'max_distance': 0,
        'nearest_exit': None,
        'exit_distance': float('inf')
    }

    visited = set()
    queue = [(start_pos, 0)] 
    directions = [(0,1), (0,-1), (1,0), (-1,0)]

    while queue:
        current_pos, distance = queue.pop(0)
        if current_pos not in visited:
            visited.add(current_pos)
            result['accessible_cells'].add(current_pos)
            result['max_distance'] = max(result['max_distance'], distance)

            free_adjacent = 0
            blocked_by_snake = 0
            for dx, dy in directions:
                next_pos = (current_pos[0] + dx, current_pos[1] + dy)

                if (0 <= next_pos[0] < grid.shape[0] and 
                    0 <= next_pos[1] < grid.shape[1]):

                    if grid[next_pos] == 0 and next_pos not in snake_body:
                        free_adjacent += 1
                        if next_pos not in visited:
                            if max_depth is None or distance < max_depth:
                                queue.append((next_pos, distance + 1))
                    elif grid[next_pos] == 2 or next_pos in snake_body:
                        blocked_by_snake += 1

            if free_adjacent <= 1 and distance > 0:
                result['dead_ends'].add(current_pos)
            elif free_adjacent >= 2:
                result['open_paths'].add(current_pos)

            cell_score = free_adjacent * (1.0 / (distance + 1))
            if free_adjacent >= 2:
                cell_score *= 1.5  
            if current_pos in result['dead_ends']:
                cell_score *= 0.5  

            result['space_score'] += cell_score

    return result

def analyze_space(grid, position, snake_body):
    flood_result = flood_fill(grid, position, snake_body)

    space_info = {
        'available_space': len(flood_result['accessible_cells']),
        'longest_path': list(flood_result['accessible_cells']),  
        'is_enclosed': len(flood_result['open_paths']) == 0,
        'nearest_exit': flood_result['nearest_exit'],
        'danger_level': len(flood_result['dead_ends']) / max(1, len(flood_result['accessible_cells'])),
        'space_score': flood_result['space_score'],
        'dead_ends': flood_result['dead_ends'],
        'open_paths': flood_result['open_paths']
    }

    visited = set()
    queue = [(0, position, [position])] 
    directions = [(0,1), (0,-1), (1,0), (-1,0)]

    while queue:
        dist, current, path = queue.pop()
        if current not in visited:
            visited.add(current)
            space_info['available_space'] += 1

            if len(path) > len(space_info['longest_path']):
                space_info['longest_path'] = path[:]

            blocked_directions = 0
            for direction in directions:
                next_pos = (current[0] + direction[0], current[1] + direction[1])
                if not (0 <= next_pos[0] < grid.shape[0] and 
                       0 <= next_pos[1] < grid.shape[1] and 
                       grid[next_pos] != 9 and 
                       grid[next_pos] != 2):
                    blocked_directions += 1
                elif next_pos not in visited:
                    new_path = path + [next_pos]
                    queue.append((dist - 1, next_pos, new_path))

            if blocked_directions >= 3:
                space_info['danger_level'] += 1

    snake_length = len(snake_body)
    space_info['is_enclosed'] = space_info['available_space'] <= snake_length * 1.5

    if space_info['is_enclosed']:
        min_exit_dist = float('inf')
        for pos in visited:
            for direction in directions:
                next_pos = (pos[0] + direction[0], pos[1] + direction[1])
                if (0 <= next_pos[0] < grid.shape[0] and 
                    0 <= next_pos[1] < grid.shape[1] and 
                    grid[next_pos] != 9 and 
                    grid[next_pos] != 2 and 
                    next_pos not in visited):
                    dist = abs(next_pos[0] - position[0]) + abs(next_pos[1] - position[1])
                    if dist < min_exit_dist:
                        min_exit_dist = dist
                        space_info['nearest_exit'] = next_pos

    return space_info

def is_dead_end(grid, position, snake_length):
    space_info = analyze_space(grid, position, [(0,0)] * snake_length)  
    return space_info['is_enclosed'] or space_info['danger_level'] > snake_length / 3

def predict_future_collision(grid, path, snake_body, snake_length):

    if not path:
        return True

    future_body = deque(snake_body)

    for pos in path:
        future_body.appendleft(pos)
        if len(future_body) > snake_length:
            future_body.pop()

        if is_dead_end(grid, pos, snake_length):
            return True

    return False

def pathChanges(path):
    directions = []
    for i in range(len(path) - 1):
        change = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        changeName = inverseDirs.get(change,"ERROR")
        directions.append(changeName)
    return directions

class PathFindingError(Exception):
    pass

def is_apple_accessible(grid, start, apple_pos, snake_body):
    space_info = analyze_space(grid, apple_pos, snake_body)
    head_to_apple = analyze_space(grid, start, snake_body)

    result = {
        'accessible': False,
        'reason': None,
        'alternative_target': None
    }

    if apple_pos in head_to_apple['visited']:
        result['accessible'] = True
        return result

    if space_info['is_enclosed']:
        result['reason'] = 'enclosed'
        max_space = 0
        best_pos = None

        for x in range(grid.shape[0]):
            for y in range(grid.shape[1]):
                if grid[x,y] != 9 and grid[x,y] != 2:  
                    pos = (x,y)
                    if pos in head_to_apple['visited']:  
                        space = analyze_space(grid, pos, snake_body)
                        if space['available_space'] > max_space:
                            max_space = space['available_space']
                            best_pos = pos

        result['alternative_target'] = best_pos
        return result
    if head_to_apple['danger_level'] > len(snake_body) / 2:
        result['reason'] = 'dangerous_path'
        result['alternative_target'] = head_to_apple['nearest_exit']
        return result

    result['accessible'] = True
    return result

class PathFindingError(Exception):
    pass

def is_apple_accessible(grid, start, apple_pos, snake_body):
    space_info = analyze_space(grid, apple_pos, snake_body)
    head_to_apple = analyze_space(grid, start, snake_body)

    result = {
        'accessible': False,
        'reason': None,
        'alternative_target': None
    }

    if apple_pos in head_to_apple['visited']:
        result['accessible'] = True
        return result

    if space_info['is_enclosed']:
        result['reason'] = 'enclosed'
        max_space = 0
        best_pos = None

        for x in range(grid.shape[0]):
            for y in range(grid.shape[1]):
                if grid[x,y] != 9 and grid[x,y] != 2:  
                    pos = (x,y)
                    if pos in head_to_apple['visited']:  
                        space = analyze_space(grid, pos, snake_body)
                        if space['available_space'] > max_space:
                            max_space = space['available_space']
                            best_pos = pos

        result['alternative_target'] = best_pos
        return result
    if head_to_apple['danger_level'] > len(snake_body) / 2:
        result['reason'] = 'dangerous_path'
        result['alternative_target'] = head_to_apple['nearest_exit']
        return result

    result['accessible'] = True
    return result

from Logger import Logger

class Calculator():
    def __init__(self):
        self.apple = None
        self.path_cache = {}  
        self.cache_limit = 1000  
        self.last_valid_path = None  
        self.recovery_attempts = 0  
        self.max_recovery_attempts = 3 
        self.alternative_target = None 
        self.logger = Logger()  

        self.last_moves = []  
        self.max_moves_history = 5 
        self.dangerous_moves = set()  
        self.last_position = None 

    def update_movement_history(self, current_pos, last_pos, success=True):
        if last_pos and current_pos:
            move = (last_pos, current_pos)
            if not success:
                self.dangerous_moves.add(move)
            self.last_moves.append(move)
            if len(self.last_moves) > self.max_moves_history:
                self.last_moves.pop(0)

    def is_move_safe(self, grid, pos, snake_body, proposed_move):
        if tuple(proposed_move) in self.dangerous_moves:
            return False

        current_space = flood_fill(grid, pos, snake_body)
        future_space = flood_fill(grid, proposed_move[1], snake_body)

        if len(future_space['accessible_cells']) < len(current_space['accessible_cells']) * 0.7:
            return False

        return True

    def compute(self, gameState):
        try:
            grid, pos, apple = gameState
            last_pos = self.last_position
            self.last_position = pos
            if last_pos and pos in self.dangerous_moves:
                self.update_movement_history(pos, last_pos, False)

            if apple is None:
                if self.last_valid_path and len(self.last_valid_path) > 1:
                    path = self.last_valid_path[1:]
                else:
                    snake_body = [(i, j) for i, j in zip(*np.where(grid == 2))]
                    path = find_safe_alternative(grid, pos, snake_body, len(snake_body), 
                                              last_move=self.last_moves[-1] if self.last_moves else None)
            else:
                snake_body = [(i, j) for i, j in zip(*np.where(grid == 2))]
                apple_status = is_apple_accessible(grid, pos, apple, snake_body)

                if not apple_status['accessible']:
                    if apple_status['alternative_target']:
                        self.alternative_target = apple_status['alternative_target']
                        path = astar(grid, pos, self.alternative_target, snake_body, self)
                    else:
                        path = find_safe_alternative(grid, pos, snake_body, len(snake_body))
                else:
                    path = astar(grid, pos, apple, snake_body, self)

            if path is None or len(path) < 2:
                snake_body = [(i, j) for i, j in zip(*np.where(grid == 2))]
                path = find_safe_alternative(grid, pos, snake_body, len(snake_body))
                if path is None:
                    path = survival_mode(grid, pos, snake_body)

            if path and len(path) >= 2:
                self.last_valid_path = path
                direction = pathChanges([path[0], path[1]])[0]
                return ["press", direction]

            if self.last_valid_path and len(self.last_valid_path) > 1:
                direction = pathChanges([self.last_valid_path[0], self.last_valid_path[1]])[0]
                return ["press", direction]

            for direction in ['up', 'right', 'down', 'left']:
                return ["press", direction]

        except Exception as e:
            error_msg = f"Error in compute: {str(e)}"
            print(error_msg)
            self.logger.log_error(error_msg)

            additional_info = (
                "Error occurred during computation\n"
                f"Recovery attempts: {self.recovery_attempts}/{self.max_recovery_attempts}\n"
                f"Has last valid path: {'Yes' if self.last_valid_path else 'No'}\n"
                f"Alternative target: {self.alternative_target}"
            )
            self.logger.log_state(grid, pos, apple, additional_info=additional_info)

            return ["press", "right"] 
        self.alternative_target = None  
        self.last = None

    def compute(self, percept):

        if percept is not None:
            path = astar(percept[0], percept[1],percept[2])

            if path is not None:
                res = pathChanges(path)
                if len(res) > 0:
                    self.last = res[0]
                    return ["press", res[0]]
            path = astar(percept[0], percept[1], percept[3])
            if path is not None:
                res = pathChanges(path)
                if len(res) > 0:
                    self.last = res[0]
                    return ["press", res[0]]
            return ["press", self.last]

        else:
            print("SOMETHING BAD HAPPENED")
            return
