def display_move_history():
    """Display the move history with mini boards in two columns"""
    st.markdown(
        '<h3 style="margin-bottom: 30px;">📜 Game History</h3>',
        unsafe_allow_html=True,
    )
    history_container = st.empty()

    if "move_history" in st.session_state and st.session_state.move_history:
        # Split moves into player 1 and player 2 moves
        p1_moves = []
        p2_moves = []
        current_board = [[" " for _ in range(3)] for _ in range(3)]

        # Process all moves first
        for move in st.session_state.move_history:
            row, col = map(int, move["move"].split(","))
            is_player1 = "Player 1" in move["player"]
            symbol = "X" if is_player1 else "O"
            current_board[row][col] = symbol
            board_copy = [row[:] for row in current_board]

            move_html = f"""<div class="move-entry player{1 if is_player1 else 2}">
                {create_mini_board_html(board_copy, (row, col), is_player1)}
                <div class="move-info">
                    <div class="move-number player{1 if is_player1 else 2}">Move #{move["number"]}</div>
                    <div>{move["player"]}</div>
                    <div style="font-size: 0.9em; color: #888">Position: ({row}, {col})</div>
                </div>
            </div>"""

            if is_player1:
                p1_moves.append(move_html)
            else:
                p2_moves.append(move_html)

        max_moves = max(len(p1_moves), len(p2_moves))
        history_content = '<div class="history-grid">'

        # Left column (Player 1)
        history_content += '<div class="history-column-left">'
        for i in range(max_moves):
            entry_html = ""
            # Player 1 move
            if i < len(p1_moves):
                entry_html += p1_moves[i]
            history_content += entry_html
        history_content += "</div>"

        # Right column (Player 2)
        history_content += '<div class="history-column-right">'
        for i in range(max_moves):
            entry_html = ""
            # Player 2 move
            if i < len(p2_moves):
                entry_html += p2_moves[i]
            history_content += entry_html
        history_content += "</div>"

        history_content += "</div>"

        # Display the content
        history_container.markdown(history_content, unsafe_allow_html=True)
    else:
        history_container.markdown(
            """<div style="text-align: center; color: #666; padding: 20px;">
                No moves yet. Start the game to see the history!
            </div>""",
            unsafe_allow_html=True,
        )