def depth_first_search(
    possible_board: list[int],
    diagonal_right_collisions: list[int],
    diagonal_left_collisions: list[int],
    boards: list[list[str]],
    n: int,
) -> None:
    row = len(possible_board)


    if row == n:

        boards.append([". " * i + "Q " + ". " * (n - 1 - i) for i in possible_board])
        return

    for col in range(n):
        if (
            col in possible_board
            or row - col in diagonal_right_collisions
            or row + col in diagonal_left_collisions
        ):
            continue

        depth_first_search(
            [*possible_board, col],
            [*diagonal_right_collisions, row - col],
            [*diagonal_left_collisions, row + col],
            boards,
            n,
        )
