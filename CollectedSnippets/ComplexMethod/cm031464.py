def _eat_identifier(cls, str, limit, pos):
        """Given a string and pos, return the number of chars in the
        identifier which ends at pos, or 0 if there is no such one.

        This ignores non-identifier eywords are not identifiers.
        """
        is_ascii_id_char = _IS_ASCII_ID_CHAR

        # Start at the end (pos) and work backwards.
        i = pos

        # Go backwards as long as the characters are valid ASCII
        # identifier characters. This is an optimization, since it
        # is faster in the common case where most of the characters
        # are ASCII.
        while i > limit and (
                ord(str[i - 1]) < 128 and
                is_ascii_id_char[ord(str[i - 1])]
        ):
            i -= 1

        # If the above loop ended due to reaching a non-ASCII
        # character, continue going backwards using the most generic
        # test for whether a string contains only valid identifier
        # characters.
        if i > limit and ord(str[i - 1]) >= 128:
            while i - 4 >= limit and ('a' + str[i - 4:pos]).isidentifier():
                i -= 4
            if i - 2 >= limit and ('a' + str[i - 2:pos]).isidentifier():
                i -= 2
            if i - 1 >= limit and ('a' + str[i - 1:pos]).isidentifier():
                i -= 1

            # The identifier candidate starts here. If it isn't a valid
            # identifier, don't eat anything. At this point that is only
            # possible if the first character isn't a valid first
            # character for an identifier.
            if not str[i:pos].isidentifier():
                return 0
        elif i < pos:
            # All characters in str[i:pos] are valid ASCII identifier
            # characters, so it is enough to check that the first is
            # valid as the first character of an identifier.
            if not _IS_ASCII_ID_FIRST_CHAR[ord(str[i])]:
                return 0

        # All keywords are valid identifiers, but should not be
        # considered identifiers here, except for True, False and None.
        if i < pos and (
                iskeyword(str[i:pos]) and
                str[i:pos] not in cls._ID_KEYWORDS
        ):
            return 0

        return pos - i