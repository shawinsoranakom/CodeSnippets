def search(
    grid: list[list[int]],
    init: list[int],
    goal: list[int],
    cost: int,
    heuristic: list[list[int]],
) -> tuple[list[list[int]], list[list[int]]]:
    closed = [
        [0 for col in range(len(grid[0]))] for row in range(len(grid))
    ] 
    closed[init[0]][init[1]] = 1
    action = [
        [0 for col in range(len(grid[0]))] for row in range(len(grid))
    ]

    x = init[0]
    y = init[1]
    g = 0
    f = g + heuristic[x][y] 
    cell = [[f, g, x, y]]

    found = False 
    resign = False 

    while not found and not resign:
        if len(cell) == 0:
            raise ValueError("Algorithm is unable to find solution")
        else: 
            cell.sort()
            cell.reverse()
            next_cell = cell.pop()
            x = next_cell[2]
            y = next_cell[3]
            g = next_cell[1]

            if x == goal[0] and y == goal[1]:
                found = True
            else:
                for i in range(len(DIRECTIONS)): 
                    x2 = x + DIRECTIONS[i][0]
                    y2 = y + DIRECTIONS[i][1]
                    if (
                        x2 >= 0
                        and x2 < len(grid)
                        and y2 >= 0
                        and y2 < len(grid[0])
                        and closed[x2][y2] == 0
                        and grid[x2][y2] == 0
                    ):
                        g2 = g + cost
                        f2 = g2 + heuristic[x2][y2]
                        cell.append([f2, g2, x2, y2])
                        closed[x2][y2] = 1
                        action[x2][y2] = i
    invpath = []
    x = goal[0]
    y = goal[1]
    invpath.append([x, y]) 
    while x != init[0] or y != init[1]:
        x2 = x - DIRECTIONS[action[x][y]][0]
        y2 = y - DIRECTIONS[action[x][y]][1]
        x = x2
        y = y2
        invpath.append([x, y])

    path = []
    for i in range(len(invpath)):
        path.append(invpath[len(invpath) - 1 - i])
    return path, action
