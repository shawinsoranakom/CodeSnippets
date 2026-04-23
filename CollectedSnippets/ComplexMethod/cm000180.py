def run_maze(
    maze: list[list[int]],
    i: int,
    j: int,
    destination_row: int,
    destination_column: int,
    solutions: list[list[int]],
) -> bool:
    """
    This method is recursive starting from (i, j) and going in one of four directions:
    up, down, left, right.
    If a path is found to destination it returns True otherwise it returns False.
    Parameters
        maze: A two dimensional matrix of zeros and ones.
        i, j : coordinates of matrix
        solutions: A two dimensional matrix of solutions.
    Returns:
        Boolean if path is found True, Otherwise False.
    """
    size = len(maze)
    # Final check point.
    if i == destination_row and j == destination_column and maze[i][j] == 0:
        solutions[i][j] = 0
        return True

    lower_flag = (not i < 0) and (not j < 0)  # Check lower bounds
    upper_flag = (i < size) and (j < size)  # Check upper bounds

    if lower_flag and upper_flag:
        # check for already visited and block points.
        block_flag = (solutions[i][j]) and (not maze[i][j])
        if block_flag:
            # check visited
            solutions[i][j] = 0

            # check for directions
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