def dedent(self, text):
        """Remove any common leading whitespace from every line in `text`.
        """
        # Look for the longest leading string of spaces and tabs common to
        # all lines.
        margin = None
        _whitespace_only_re = re.compile('^[ \t]+$', re.MULTILINE)
        _leading_whitespace_re = re.compile('(^[ \t]*)(?:[^ \t\n])', re.MULTILINE)
        text = _whitespace_only_re.sub('', text)
        indents = _leading_whitespace_re.findall(text)
        for indent in indents:
            if margin is None:
                margin = indent

            # Current line more deeply indented than previous winner:
            # no change (previous winner is still on top).
            elif indent.startswith(margin):
                pass

            # Current line consistent with and no deeper than previous winner:
            # it's the new winner.
            elif margin.startswith(indent):
                margin = indent

            # Find the largest common whitespace between current line and previous
            # winner.
            else:
                for i, (x, y) in enumerate(zip(margin, indent)):
                    if x != y:
                        margin = margin[:i]
                        break

        # sanity check (testing/debugging only)
        if 0 and margin:
            for line in text.split("\n"):
                assert not line or line.startswith(margin), \
                    "line = %r, margin = %r" % (line, margin)

        if margin:
            text = re.sub(r'(?m)^' + margin, '', text)
            return text, len(margin)
        else:
            return text, 0