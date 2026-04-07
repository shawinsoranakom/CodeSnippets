def assertHTMLNotEqual(self, html1, html2, msg=None):
        """Assert that two HTML snippets are not semantically equivalent."""
        dom1 = assert_and_parse_html(
            self, html1, msg, "First argument is not valid HTML:"
        )
        dom2 = assert_and_parse_html(
            self, html2, msg, "Second argument is not valid HTML:"
        )

        if dom1 == dom2:
            standardMsg = "%s == %s" % (safe_repr(dom1, True), safe_repr(dom2, True))
            self.fail(self._formatMessage(msg, standardMsg))