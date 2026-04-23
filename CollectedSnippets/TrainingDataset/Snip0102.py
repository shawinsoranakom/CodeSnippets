def n_queens_solution(n: int) -> None:
    boards: list[list[str]] = []
    depth_first_search([], [], [], boards, n)

    for board in boards:
        for column in board:
            print(column)
        print("")

    print(len(boards), "solutions were found.")
