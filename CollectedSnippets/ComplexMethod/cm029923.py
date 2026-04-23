def untokenize(self, iterable):
        it = iter(iterable)
        indents = []
        startline = False
        for t in it:
            if len(t) == 2:
                self.compat(t, it)
                break
            tok_type, token, start, end, line = t
            if tok_type == ENCODING:
                self.encoding = token
                continue
            if tok_type == ENDMARKER:
                break
            if tok_type == INDENT:
                indents.append(token)
                continue
            elif tok_type == DEDENT:
                indents.pop()
                self.prev_row, self.prev_col = end
                continue
            elif tok_type in (NEWLINE, NL):
                startline = True
            elif startline and indents:
                indent = indents[-1]
                if start[1] >= len(indent):
                    self.tokens.append(indent)
                    self.prev_col = len(indent)
                startline = False
            elif tok_type in {FSTRING_MIDDLE, TSTRING_MIDDLE}:
                if '{' in token or '}' in token:
                    token = self.escape_brackets(token)
                    last_line = token.splitlines()[-1]
                    end_line, end_col = end
                    extra_chars = last_line.count("{{") + last_line.count("}}")
                    end = (end_line, end_col + extra_chars)

            self.add_whitespace(start)
            self.tokens.append(token)
            self.prev_row, self.prev_col = end
            if tok_type in (NEWLINE, NL):
                self.prev_row += 1
                self.prev_col = 0
            self.prev_type = tok_type
            self.prev_line = line
        return "".join(self.tokens)