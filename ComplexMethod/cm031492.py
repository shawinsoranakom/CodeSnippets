def _study2(self):
        """
        study1 was sufficient to determine the continuation status,
        but doing more requires looking at every character.  study2
        does this for the last interesting statement in the block.
        Creates:
            self.stmt_start, stmt_end
                slice indices of last interesting stmt
            self.stmt_bracketing
                the bracketing structure of the last interesting stmt; for
                example, for the statement "say(boo) or die",
                stmt_bracketing will be ((0, 0), (0, 1), (2, 0), (2, 1),
                (4, 0)). Strings and comments are treated as brackets, for
                the matter.
            self.lastch
                last interesting character before optional trailing comment
            self.lastopenbracketpos
                if continuation is C_BRACKET, index of last open bracket
        """
        if self.study_level >= 2:
            return
        self._study1()
        self.study_level = 2

        # Set p and q to slice indices of last interesting stmt.
        code, goodlines = self.code, self.goodlines
        i = len(goodlines) - 1  # Index of newest line.
        p = len(code)  # End of goodlines[i]
        while i:
            assert p
            # Make p be the index of the stmt at line number goodlines[i].
            # Move p back to the stmt at line number goodlines[i-1].
            q = p
            for nothing in range(goodlines[i-1], goodlines[i]):
                # tricky: sets p to 0 if no preceding newline
                p = code.rfind('\n', 0, p-1) + 1
            # The stmt code[p:q] isn't a continuation, but may be blank
            # or a non-indenting comment line.
            if  _junkre(code, p):
                i = i-1
            else:
                break
        if i == 0:
            # nothing but junk!
            assert p == 0
            q = p
        self.stmt_start, self.stmt_end = p, q

        # Analyze this stmt, to find the last open bracket (if any)
        # and last interesting character (if any).
        lastch = ""
        stack = []  # stack of open bracket indices
        push_stack = stack.append
        bracketing = [(p, 0)]
        while p < q:
            # suck up all except ()[]{}'"#\\
            m = _chew_ordinaryre(code, p, q)
            if m:
                # we skipped at least one boring char
                newp = m.end()
                # back up over totally boring whitespace
                i = newp - 1    # index of last boring char
                while i >= p and code[i] in " \t\n":
                    i = i-1
                if i >= p:
                    lastch = code[i]
                p = newp
                if p >= q:
                    break

            ch = code[p]

            if ch in "([{":
                push_stack(p)
                bracketing.append((p, len(stack)))
                lastch = ch
                p = p+1
                continue

            if ch in ")]}":
                if stack:
                    del stack[-1]
                lastch = ch
                p = p+1
                bracketing.append((p, len(stack)))
                continue

            if ch == '"' or ch == "'":
                # consume string
                # Note that study1 did this with a Python loop, but
                # we use a regexp here; the reason is speed in both
                # cases; the string may be huge, but study1 pre-squashed
                # strings to a couple of characters per line.  study1
                # also needed to keep track of newlines, and we don't
                # have to.
                bracketing.append((p, len(stack)+1))
                lastch = ch
                p = _match_stringre(code, p, q).end()
                bracketing.append((p, len(stack)))
                continue

            if ch == '#':
                # consume comment and trailing newline
                bracketing.append((p, len(stack)+1))
                p = code.find('\n', p, q) + 1
                assert p > 0
                bracketing.append((p, len(stack)))
                continue

            assert ch == '\\'
            p = p+1     # beyond backslash
            assert p < q
            if code[p] != '\n':
                # the program is invalid, but can't complain
                lastch = ch + code[p]
            p = p+1     # beyond escaped char

        # end while p < q:

        self.lastch = lastch
        self.lastopenbracketpos = stack[-1] if stack else None
        self.stmt_bracketing = tuple(bracketing)