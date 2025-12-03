def print_solution(grid: Matrix) -> None:
    for row in grid:
        for cell in row:
            print(cell, end=" ")
        print()
