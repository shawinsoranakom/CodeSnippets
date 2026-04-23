def _combine(self, other, connector, reversed):
        if not isinstance(other, LexemeCombinable):
            raise TypeError(
                "A Lexeme can only be combined with another Lexeme, "
                f"got {other.__class__.__name__}."
            )
        if reversed:
            return CombinedLexeme(other, connector, self)
        return CombinedLexeme(self, connector, other)