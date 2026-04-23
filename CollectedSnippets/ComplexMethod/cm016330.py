def is_set(self, i: int) -> bool:
        t = self.tokens[i]
        after = i < len(self.tokens) - 1 and self.tokens[i + 1]
        if t.string == "Set" and t.type == token.NAME:
            # pyrefly: ignore [bad-return]
            return after and after.string == "[" and after.type == token.OP
        return (
            (t.string == "set" and t.type == token.NAME)
            and not (i and self.tokens[i - 1].string in ("def", "."))
            and not (after and after.string == "=" and after.type == token.OP)
        )