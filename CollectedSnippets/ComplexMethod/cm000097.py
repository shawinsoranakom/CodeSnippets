def insert_northeast(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_northeast("cat", [2], [0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, None, 't'],
        [None, 'a', None],
        ['c', None, None]]
        >>> ws.insert_northeast("at", [0, 1], [2, 1, 0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, 't', 't'],
        ['a', 'a', None],
        ['c', None, None]]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Check if there is space for the word above the row
            if word_length > row + 1:
                continue

            # Attempt to insert the word into each column
            for col in cols:
                # Check if there is space to the right of the word as well as above
                if word_length + col > self.width:
                    continue

                # Check if there are existing letters
                # to the right of the column that will be overwritten
                letters_diagonal_left = [
                    self.board[row - i][col + i] for i in range(word_length)
                ]
                if all(letter is None for letter in letters_diagonal_left):
                    # Successful, insert the word northeast
                    for i in range(word_length):
                        self.board[row - i][col + i] = word[i]
                    return