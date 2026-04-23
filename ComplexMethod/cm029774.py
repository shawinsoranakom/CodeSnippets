def output_difference(self, example, got, optionflags):
        """
        Return a string describing the differences between the
        expected output for a given example (`example`) and the actual
        output (`got`).  `optionflags` is the set of option flags used
        to compare `want` and `got`.
        """
        want = example.want
        # If <BLANKLINE>s are being used, then replace blank lines
        # with <BLANKLINE> in the actual output string.
        if not (optionflags & DONT_ACCEPT_BLANKLINE):
            got = re.sub('(?m)^[ ]*(?=\n)', BLANKLINE_MARKER, got)

        # Check if we should use diff.
        if self._do_a_fancy_diff(want, got, optionflags):
            # Split want & got into lines.
            want_lines = want.splitlines(keepends=True)
            got_lines = got.splitlines(keepends=True)
            # Use difflib to find their differences.
            if optionflags & REPORT_UDIFF:
                diff = difflib.unified_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:] # strip the diff header
                kind = 'unified diff with -expected +actual'
            elif optionflags & REPORT_CDIFF:
                diff = difflib.context_diff(want_lines, got_lines, n=2)
                diff = list(diff)[2:] # strip the diff header
                kind = 'context diff with expected followed by actual'
            elif optionflags & REPORT_NDIFF:
                engine = difflib.Differ(charjunk=difflib.IS_CHARACTER_JUNK)
                diff = list(engine.compare(want_lines, got_lines))
                kind = 'ndiff with -expected +actual'
            else:
                assert 0, 'Bad diff option'
            return 'Differences (%s):\n' % kind + _indent(''.join(diff))

        # If we're not using diff, then simply list the expected
        # output followed by the actual output.
        if want and got:
            return 'Expected:\n%sGot:\n%s' % (_indent(want), _indent(got))
        elif want:
            return 'Expected:\n%sGot nothing\n' % _indent(want)
        elif got:
            return 'Expected nothing\nGot:\n%s' % _indent(got)
        else:
            return 'Expected nothing\nGot nothing\n'