def is_braced_set(self, begin: int, end: int) -> bool:
        if (
            begin + 1 == end
            or self.tokens[begin].string != "{"
            or begin
            and self.tokens[begin - 1].string == "in"  # skip `x in {1, 2, 3}`
        ):
            return False

        i = begin + 1
        empty = True
        while i < end:
            t = self.tokens[i]
            if t.type == token.OP and t.string in (":", "**"):
                return False
            if brace_end := self.bracket_pairs.get(i):
                # Skip to the end of a subexpression
                i = brace_end
            elif not is_empty(t):
                empty = False
            i += 1
        return not empty