def peek(self) -> tokenize.TokenInfo:
        """Return the next token *without* updating the index."""
        while self._index == len(self._tokens):
            tok = next(self._tokengen)
            if tok.type in (tokenize.NL, tokenize.COMMENT):
                continue
            if tok.type == token.ERRORTOKEN and tok.string.isspace():
                continue
            if (
                tok.type == token.NEWLINE
                and self._tokens
                and self._tokens[-1].type == token.NEWLINE
            ):
                continue
            self._tokens.append(tok)
            if not self._path:
                self._lines[tok.start[0]] = tok.line
        return self._tokens[self._index]