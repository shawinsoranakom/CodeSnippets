def insert_southeast(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_southeast("cat", [0], [0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [['c', None, None],
        [None, 'a', None],
        [None, None, 't']]
        >>> ws.insert_southeast("at", [1, 0], [2, 1, 0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [['c', None, None],
        ['a', 'a', None],
        [None, 't', 't']]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Check if there is space for the word below the row
            if word_length + row > self.height:
                continue

            # Attempt to insert the word into each column
            for col in cols:
                # Check if there is space to the right of the word as well as below
                if word_length + col > self.width:
                    continue

                # Check if there are existing letters
                # to the right of the column that will be overwritten
                letters_diagonal_left = [
                    self.board[row + i][col + i] for i in range(word_length)
                ]
                if all(letter is None for letter in letters_diagonal_left):
                    # Successful, insert the word southeast
                    for i in range(word_length):
                        self.board[row + i][col + i] = word[i]
                    return