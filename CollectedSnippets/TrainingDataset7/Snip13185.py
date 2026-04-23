def tokenize(self):
        """
        Split a template string into tokens and annotates each token with its
        start and end position in the source. This is slower than the default
        lexer so only use it when debug is True.
        """
        # For maintainability, it is helpful if the implementation below can
        # continue to closely parallel Lexer.tokenize()'s implementation.
        in_tag = False
        lineno = 1
        result = []
        for token_string, position in self._tag_re_split():
            if token_string:
                result.append(self.create_token(token_string, position, lineno, in_tag))
                lineno += token_string.count("\n")
            in_tag = not in_tag
        return result