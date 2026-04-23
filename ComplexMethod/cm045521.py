def validate_turn(board: Board, player: Literal["white", "black"]) -> None:
    """Validate that it is the player's turn to move."""
    last_move = board.peek() if board.move_stack else None
    if last_move is not None:
        if player == "white" and board.color_at(last_move.to_square) == WHITE:
            raise ValueError("It is not your turn to move. Wait for black to move.")
        if player == "black" and board.color_at(last_move.to_square) == BLACK:
            raise ValueError("It is not your turn to move. Wait for white to move.")
    elif last_move is None and player != "white":
        raise ValueError("It is not your turn to move. Wait for white to move first.")