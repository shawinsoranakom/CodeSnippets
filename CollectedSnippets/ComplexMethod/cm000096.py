def insert_north(self, word: str, rows: list[int], cols: list[int]) -> None:
        """
        >>> ws = WordSearch(WORDS, 3, 3)
        >>> ws.insert_north("cat", [2], [2])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, None, 't'],
        [None, None, 'a'],
        [None, None, 'c']]
        >>> ws.insert_north("at", [0, 1, 2], [2, 1])
        >>> ws.board  # doctest: +NORMALIZE_WHITESPACE
        [[None, 't', 't'],
        [None, 'a', 'a'],
        [None, None, 'c']]
        """
        word_length = len(word)
        # Attempt to insert the word into each row and when successful, exit
        for row in rows:
            # Check if there is space above the row to fit in the word
            if word_length > row + 1:
                continue

            # Attempt to insert the word into each column
            for col in cols:
                # Only check to be made here is if there are existing letters
                # above the column that will be overwritten
                letters_above = [self.board[row - i][col] for i in range(word_length)]
                if all(letter is None for letter in letters_above):
                    # Successful, insert the word north
                    for i in range(word_length):
                        self.board[row - i][col] = word[i]
                    return