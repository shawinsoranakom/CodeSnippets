def compute_backslash_indent(self):
        """Return number of spaces the next line should be indented.

        Line continuation must be C_BACKSLASH.  Also assume that the new
        line is the first one following the initial line of the stmt.
        """
        self._study2()
        assert self.continuation == C_BACKSLASH
        code = self.code
        i = self.stmt_start
        while code[i] in " \t":
            i = i+1
        startpos = i

        # See whether the initial line starts an assignment stmt; i.e.,
        # look for an = operator
        endpos = code.find('\n', startpos) + 1
        found = level = 0
        while i < endpos:
            ch = code[i]
            if ch in "([{":
                level = level + 1
                i = i+1
            elif ch in ")]}":
                if level:
                    level = level - 1
                i = i+1
            elif ch == '"' or ch == "'":
                i = _match_stringre(code, i, endpos).end()
            elif ch == '#':
                # This line is unreachable because the # makes a comment of
                # everything after it.
                break
            elif level == 0 and ch == '=' and \
                   (i == 0 or code[i-1] not in "=<>!") and \
                   code[i+1] != '=':
                found = 1
                break
            else:
                i = i+1

        if found:
            # found a legit =, but it may be the last interesting
            # thing on the line
            i = i+1     # move beyond the =
            found = re.match(r"\s*\\", code[i:endpos]) is None

        if not found:
            # oh well ... settle for moving beyond the first chunk
            # of non-whitespace chars
            i = startpos
            while code[i] not in " \t\n":
                i = i+1

        return len(code[self.stmt_start:i].expandtabs(\
                                     self.tabwidth)) + 1