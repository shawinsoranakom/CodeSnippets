def insert_west(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_west("cat", [1], [2])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, None, None],
        ['t', 'a', 'c'],
        [None, None, None]]
        >>> ws.insert_west("at", [1, 0], [1, 2, 0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [['t', 'a', None],
        ['t', 'a', 'c'],
        [None, None, None]]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Attempt to insert the word into each column
            for col in cols:
                # Check if there is space to the left of the word
                if word_length > col + 1:
                    continue

                # Check if there are existing letters
                # to the left of the column that will be overwritten
                letters_left = [self.board[row][col - i] for i in range(word_length)]
                if all(letter is None for letter in letters_left):
                    # Successful, insert the word west
                    for i in range(word_length):
                        self.board[row][col - i] = word[i]
                    return