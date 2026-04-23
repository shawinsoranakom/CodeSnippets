def find_good_parse_start(self, is_char_in_string):
        """
        Return index of a good place to begin parsing, as close to the
        end of the string as possible.  This will be the start of some
        popular stmt like "if" or "def".  Return None if none found:
        the caller should pass more prior context then, if possible, or
        if not (the entire program text up until the point of interest
        has already been tried) pass 0 to set_lo().

        This will be reliable iff given a reliable is_char_in_string()
        function, meaning that when it says "no", it's absolutely
        guaranteed that the char is not in a string.
        """
        code, pos = self.code, None

        # Peek back from the end for a good place to start,
        # but don't try too often; pos will be left None, or
        # bumped to a legitimate synch point.
        limit = len(code)
        for tries in range(5):
            i = code.rfind(":\n", 0, limit)
            if i < 0:
                break
            i = code.rfind('\n', 0, i) + 1  # start of colon line (-1+1=0)
            m = _synchre(code, i, limit)
            if m and not is_char_in_string(m.start()):
                pos = m.start()
                break
            limit = i
        if pos is None:
            # Nothing looks like a block-opener, or stuff does
            # but is_char_in_string keeps returning true; most likely
            # we're in or near a giant string, the colorizer hasn't
            # caught up enough to be helpful, or there simply *aren't*
            # any interesting stmts.  In any of these cases we're
            # going to have to parse the whole thing to be sure, so
            # give it one last try from the start, but stop wasting
            # time here regardless of the outcome.
            m = _synchre(code)
            if m and not is_char_in_string(m.start()):
                pos = m.start()
            return pos

        # Peeking back worked; look forward until _synchre no longer
        # matches.
        i = pos + 1
        while m := _synchre(code, i):
            s, i = m.span()
            if not is_char_in_string(s):
                pos = s
        return pos