def check_output(self, want, got, optionflags):
        """
        Return True iff the actual output from an example (`got`)
        matches the expected output (`want`).  These strings are
        always considered to match if they are identical; but
        depending on what option flags the test runner is using,
        several non-exact match types are also possible.  See the
        documentation for `TestRunner` for more information about
        option flags.
        """

        # If `want` contains hex-escaped character such as "\u1234",
        # then `want` is a string of six characters(e.g. [\,u,1,2,3,4]).
        # On the other hand, `got` could be another sequence of
        # characters such as [\u1234], so `want` and `got` should
        # be folded to hex-escaped ASCII string to compare.
        got = self._toAscii(got)
        want = self._toAscii(want)

        # Handle the common case first, for efficiency:
        # if they're string-identical, always return true.
        if got == want:
            return True

        # The values True and False replaced 1 and 0 as the return
        # value for boolean comparisons in Python 2.3.
        if not (optionflags & DONT_ACCEPT_TRUE_FOR_1):
            if (got,want) == ("True\n", "1\n"):
                return True
            if (got,want) == ("False\n", "0\n"):
                return True

        # <BLANKLINE> can be used as a special sequence to signify a
        # blank line, unless the DONT_ACCEPT_BLANKLINE flag is used.
        if not (optionflags & DONT_ACCEPT_BLANKLINE):
            # Replace <BLANKLINE> in want with a blank line.
            want = re.sub(r'(?m)^%s\s*?$' % re.escape(BLANKLINE_MARKER),
                          '', want)
            # If a line in got contains only spaces, then remove the
            # spaces.
            got = re.sub(r'(?m)^[^\S\n]+$', '', got)
            if got == want:
                return True

        # This flag causes doctest to ignore any differences in the
        # contents of whitespace strings.  Note that this can be used
        # in conjunction with the ELLIPSIS flag.
        if optionflags & NORMALIZE_WHITESPACE:
            got = ' '.join(got.split())
            want = ' '.join(want.split())
            if got == want:
                return True

        # The ELLIPSIS flag says to let the sequence "..." in `want`
        # match any substring in `got`.
        if optionflags & ELLIPSIS:
            if _ellipsis_match(want, got):
                return True

        # We didn't find any match; return false.
        return False