def run_maze(
    maze: list[list[int]],
    i: int,
    j: int,
    destination_row: int,
    destination_column: int,
    solutions: list[list[int]],
) -> bool:
    size = len(maze)
    if i == destination_row and j == destination_column and maze[i][j] == 0:
        solutions[i][j] = 0
        return True

    lower_flag = (not i < 0) and (not j < 0)  
    upper_flag = (i < size) and (j < size)  

    if lower_flag and upper_flag:
        block_flag = (solutions[i][j]) and (not maze[i][j])
        if block_flag:
            solutions[i][j] = 0

            if (
                run_maze(maze, i + 1, j, destination_row, destination_column, solutions)
                or run_maze(
                    maze, i, j + 1, destination_row, destination_column, solutions
                )
                or run_maze(
                    maze, i - 1, j, destination_row, destination_column, solutions
                )
                or run_maze(
                    maze, i, j - 1, destination_row, destination_column, solutions
                )
            ):
                return True

            solutions[i][j] = 1
            return False
    return False
