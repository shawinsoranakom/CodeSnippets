def get_expression(self):
        """Return a string with the Python expression which ends at the
        given index, which is empty if there is no real one.
        """
        if not self.is_in_code():
            raise ValueError("get_expression should only be called "
                             "if index is inside a code.")

        rawtext = self.rawtext
        bracketing = self.bracketing

        brck_index = self.indexbracket
        brck_limit = bracketing[brck_index][0]
        pos = self.indexinrawtext

        last_identifier_pos = pos
        postdot_phase = True

        while True:
            # Eat whitespaces, comments, and if postdot_phase is False - a dot
            while True:
                if pos>brck_limit and rawtext[pos-1] in self._whitespace_chars:
                    # Eat a whitespace
                    pos -= 1
                elif (not postdot_phase and
                      pos > brck_limit and rawtext[pos-1] == '.'):
                    # Eat a dot
                    pos -= 1
                    postdot_phase = True
                # The next line will fail if we are *inside* a comment,
                # but we shouldn't be.
                elif (pos == brck_limit and brck_index > 0 and
                      rawtext[bracketing[brck_index-1][0]] == '#'):
                    # Eat a comment
                    brck_index -= 2
                    brck_limit = bracketing[brck_index][0]
                    pos = bracketing[brck_index+1][0]
                else:
                    # If we didn't eat anything, quit.
                    break

            if not postdot_phase:
                # We didn't find a dot, so the expression end at the
                # last identifier pos.
                break

            ret = self._eat_identifier(rawtext, brck_limit, pos)
            if ret:
                # There is an identifier to eat
                pos = pos - ret
                last_identifier_pos = pos
                # Now, to continue the search, we must find a dot.
                postdot_phase = False
                # (the loop continues now)

            elif pos == brck_limit:
                # We are at a bracketing limit. If it is a closing
                # bracket, eat the bracket, otherwise, stop the search.
                level = bracketing[brck_index][1]
                while brck_index > 0 and bracketing[brck_index-1][1] > level:
                    brck_index -= 1
                if bracketing[brck_index][0] == brck_limit:
                    # We were not at the end of a closing bracket
                    break
                pos = bracketing[brck_index][0]
                brck_index -= 1
                brck_limit = bracketing[brck_index][0]
                last_identifier_pos = pos
                if rawtext[pos] in "([":
                    # [] and () may be used after an identifier, so we
                    # continue. postdot_phase is True, so we don't allow a dot.
                    pass
                else:
                    # We can't continue after other types of brackets
                    if rawtext[pos] in "'\"":
                        # Scan a string prefix
                        while pos > 0 and rawtext[pos - 1] in "rRbBuU":
                            pos -= 1
                        last_identifier_pos = pos
                    break

            else:
                # We've found an operator or something.
                break

        return rawtext[last_identifier_pos:self.indexinrawtext]