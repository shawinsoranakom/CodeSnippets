def insert_south(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_south("cat", [0], [0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [['c', None, None],
        ['a', None, None],
        ['t', None, None]]
        >>> ws.insert_south("at", [2, 1, 0], [0, 1, 2])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [['c', None, None],
        ['a', 'a', None],
        ['t', 't', None]]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Check if there is space below the row to fit in the word
            if word_length + row > self.height:
                continue

            # Attempt to insert the word into each column
            for col in cols:
                # Only check to be made here is if there are existing letters
                # below the column that will be overwritten
                letters_below = [self.board[row + i][col] for i in range(word_length)]
                if all(letter is None for letter in letters_below):
                    # Successful, insert the word south
                    for i in range(word_length):
                        self.board[row + i][col] = word[i]
                    return