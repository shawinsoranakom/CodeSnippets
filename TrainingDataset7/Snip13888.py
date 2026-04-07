def assertHTMLEqual(self, html1, html2, msg=None):
        """
        Assert that two HTML snippets are semantically the same.
        Whitespace in most cases is ignored, and attribute ordering is not
        significant. The arguments must be valid HTML.
        """
        dom1 = assert_and_parse_html(
            self, html1, msg, "First argument is not valid HTML:"
        )
        dom2 = assert_and_parse_html(
            self, html2, msg, "Second argument is not valid HTML:"
        )

        if dom1 != dom2:
            standardMsg = "%s != %s" % (safe_repr(dom1, True), safe_repr(dom2, True))
            diff = "\n" + "\n".join(
                difflib.ndiff(
                    str(dom1).splitlines(),
                    str(dom2).splitlines(),
                )
            )
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))