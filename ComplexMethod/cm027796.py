def execute_move(move: str) -> str:
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move not in st.session_state.board.legal_moves:
            return f"Invalid move: {move}. Please call available_moves() to see valid moves."

        # Update board state
        st.session_state.board.push(chess_move)
        st.session_state.made_move = True

        # Generate and store board visualization
        board_svg = chess.svg.board(st.session_state.board,
                                  arrows=[(chess_move.from_square, chess_move.to_square)],
                                  fill={chess_move.from_square: "gray"},
                                  size=400)
        st.session_state.board_svg = board_svg
        st.session_state.move_history.append(board_svg)

        # Get piece information
        moved_piece = st.session_state.board.piece_at(chess_move.to_square)
        piece_unicode = moved_piece.unicode_symbol()
        piece_type_name = chess.piece_name(moved_piece.piece_type)
        piece_name = piece_type_name.capitalize() if piece_unicode.isupper() else piece_type_name

        # Generate move description
        from_square = chess.SQUARE_NAMES[chess_move.from_square]
        to_square = chess.SQUARE_NAMES[chess_move.to_square]
        move_desc = f"Moved {piece_name} ({piece_unicode}) from {from_square} to {to_square}."
        if st.session_state.board.is_checkmate():
            winner = 'White' if st.session_state.board.turn == chess.BLACK else 'Black'
            move_desc += f"\nCheckmate! {winner} wins!"
        elif st.session_state.board.is_stalemate():
            move_desc += "\nGame ended in stalemate!"
        elif st.session_state.board.is_insufficient_material():
            move_desc += "\nGame ended - insufficient material to checkmate!"
        elif st.session_state.board.is_check():
            move_desc += "\nCheck!"

        return move_desc
    except ValueError:
        return f"Invalid move format: {move}. Please use UCI format (e.g., 'e2e4')."