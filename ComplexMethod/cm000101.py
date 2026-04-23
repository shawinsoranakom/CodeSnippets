def insert_southwest(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_southwest("cat", [0], [2])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, None, 'c'],
        [None, 'a', None],
        ['t', None, None]]
        >>> ws.insert_southwest("at", [1, 2], [2, 1, 0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, None, 'c'],
        [None, 'a', 'a'],
        ['t', 't', None]]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Check if there is space for the word below the row
            if word_length + row > self.height:
                continue

            # Attempt to insert the word into each column
            for col in cols:
                # Check if there is space to the left of the word as well as below
                if word_length > col + 1:
                    continue

                # Check if there are existing letters
                # to the right of the column that will be overwritten
                letters_diagonal_left = [
                    self.board[row + i][col - i] for i in range(word_length)
                ]
                if all(letter is None for letter in letters_diagonal_left):
                    # Successful, insert the word southwest
                    for i in range(word_length):
                        self.board[row + i][col - i] = word[i]
                    return