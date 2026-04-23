def compat(self, token, iterable):
        indents = []
        toks_append = self.tokens.append
        startline = token[0] in (NEWLINE, NL)
        prevstring = False
        in_fstring_or_tstring = 0

        for tok in _itertools.chain([token], iterable):
            toknum, tokval = tok[:2]
            if toknum == ENCODING:
                self.encoding = tokval
                continue

            if toknum in (NAME, NUMBER):
                tokval += ' '

            # Insert a space between two consecutive strings
            if toknum == STRING:
                if prevstring:
                    tokval = ' ' + tokval
                prevstring = True
            else:
                prevstring = False

            if toknum in {FSTRING_START, TSTRING_START}:
                in_fstring_or_tstring += 1
            elif toknum in {FSTRING_END, TSTRING_END}:
                in_fstring_or_tstring -= 1
            if toknum == INDENT:
                indents.append(tokval)
                continue
            elif toknum == DEDENT:
                indents.pop()
                continue
            elif toknum in (NEWLINE, NL):
                startline = True
            elif startline and indents:
                toks_append(indents[-1])
                startline = False
            elif toknum in {FSTRING_MIDDLE, TSTRING_MIDDLE}:
                tokval = self.escape_brackets(tokval)

            # Insert a space between two consecutive brackets if we are in an f-string or t-string
            if tokval in {"{", "}"} and self.tokens and self.tokens[-1] == tokval and in_fstring_or_tstring:
                tokval = ' ' + tokval

            # Insert a space between two consecutive f-strings
            if toknum in (STRING, FSTRING_START) and self.prev_type in (STRING, FSTRING_END):
                self.tokens.append(" ")

            toks_append(tokval)
            self.prev_type = toknum