def check_winner(self) -> Optional[str]:
        """
        Check if there's a winner.

        Returns:
            Optional[str]: The winning player (X or O) or None if no winner
        """
        # Check rows
        for row in self.board:
            if row.count(row[0]) == 3 and row[0] != EMPTY:
                return row[0]

        # Check columns
        for col in range(3):
            column = [self.board[row][col] for row in range(3)]
            if column.count(column[0]) == 3 and column[0] != EMPTY:
                return column[0]

        # Check diagonals
        diagonal1 = [self.board[i][i] for i in range(3)]
        if diagonal1.count(diagonal1[0]) == 3 and diagonal1[0] != EMPTY:
            return diagonal1[0]

        diagonal2 = [self.board[i][2 - i] for i in range(3)]
        if diagonal2.count(diagonal2[0]) == 3 and diagonal2[0] != EMPTY:
            return diagonal2[0]

        return None