def _study1(self):
        """Find the line numbers of non-continuation lines.

        As quickly as humanly possible <wink>, find the line numbers (0-
        based) of the non-continuation lines.
        Creates self.{goodlines, continuation}.
        """
        if self.study_level >= 1:
            return
        self.study_level = 1

        # Map all uninteresting characters to "x", all open brackets
        # to "(", all close brackets to ")", then collapse runs of
        # uninteresting characters.  This can cut the number of chars
        # by a factor of 10-40, and so greatly speed the following loop.
        code = self.code
        code = code.translate(trans)
        code = code.replace('xxxxxxxx', 'x')
        code = code.replace('xxxx', 'x')
        code = code.replace('xx', 'x')
        code = code.replace('xx', 'x')
        code = code.replace('\nx', '\n')
        # Replacing x\n with \n would be incorrect because
        # x may be preceded by a backslash.

        # March over the squashed version of the program, accumulating
        # the line numbers of non-continued stmts, and determining
        # whether & why the last stmt is a continuation.
        continuation = C_NONE
        level = lno = 0     # level is nesting level; lno is line number
        self.goodlines = goodlines = [0]
        push_good = goodlines.append
        i, n = 0, len(code)
        while i < n:
            ch = code[i]
            i = i+1

            # cases are checked in decreasing order of frequency
            if ch == 'x':
                continue

            if ch == '\n':
                lno = lno + 1
                if level == 0:
                    push_good(lno)
                    # else we're in an unclosed bracket structure
                continue

            if ch == '(':
                level = level + 1
                continue

            if ch == ')':
                if level:
                    level = level - 1
                    # else the program is invalid, but we can't complain
                continue

            if ch == '"' or ch == "'":
                # consume the string
                quote = ch
                if code[i-1:i+2] == quote * 3:
                    quote = quote * 3
                firstlno = lno
                w = len(quote) - 1
                i = i+w
                while i < n:
                    ch = code[i]
                    i = i+1

                    if ch == 'x':
                        continue

                    if code[i-1:i+w] == quote:
                        i = i+w
                        break

                    if ch == '\n':
                        lno = lno + 1
                        if w == 0:
                            # unterminated single-quoted string
                            if level == 0:
                                push_good(lno)
                            break
                        continue

                    if ch == '\\':
                        assert i < n
                        if code[i] == '\n':
                            lno = lno + 1
                        i = i+1
                        continue

                    # else comment char or paren inside string

                else:
                    # didn't break out of the loop, so we're still
                    # inside a string
                    if (lno - 1) == firstlno:
                        # before the previous \n in code, we were in the first
                        # line of the string
                        continuation = C_STRING_FIRST_LINE
                    else:
                        continuation = C_STRING_NEXT_LINES
                continue    # with outer loop

            if ch == '#':
                # consume the comment
                i = code.find('\n', i)
                assert i >= 0
                continue

            assert ch == '\\'
            assert i < n
            if code[i] == '\n':
                lno = lno + 1
                if i+1 == n:
                    continuation = C_BACKSLASH
            i = i+1

        # The last stmt may be continued for all 3 reasons.
        # String continuation takes precedence over bracket
        # continuation, which beats backslash continuation.
        if (continuation != C_STRING_FIRST_LINE
            and continuation != C_STRING_NEXT_LINES and level > 0):
            continuation = C_BRACKET
        self.continuation = continuation

        # Push the final line number as a sentinel value, regardless of
        # whether it's continued.
        assert (continuation == C_NONE) == (goodlines[-1] == lno)
        if goodlines[-1] != lno:
            push_good(lno)