def insert_east(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_east("cat", [1], [0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, None, None],
        ['c', 'a', 't'],
        [None, None, None]]
        >>> ws.insert_east("at", [1, 0], [2, 1, 0])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, 'a', 't'],
        ['c', 'a', 't'],
        [None, None, None]]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Attempt to insert the word into each column
            for col in cols:
                # Check if there is space to the right of the word
                if word_length + col > self.width:
                    continue

                # Check if there are existing letters
                # to the right of the column that will be overwritten
                letters_left = [self.board[row][col + i] for i in range(word_length)]
                if all(letter is None for letter in letters_left):
                    # Successful, insert the word east
                    for i in range(word_length):
                        self.board[row][col + i] = word[i]
                    return