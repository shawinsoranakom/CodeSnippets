def test_escape(self):
        items = (
            ("&", "&amp;"),
            ("<", "&lt;"),
            (">", "&gt;"),
            ('"', "&quot;"),
            ("'", "&#x27;"),
        )
        # Substitution patterns for testing the above items.
        patterns = ("%s", "asdf%sfdsa", "%s1", "1%sb")
        for value, output in items:
            with self.subTest(value=value, output=output):
                for pattern in patterns:
                    with self.subTest(value=value, output=output, pattern=pattern):
                        self.check_output(escape, pattern % value, pattern % output)
                        self.check_output(
                            escape, lazystr(pattern % value), pattern % output
                        )
                # Check repeated values.
                self.check_output(escape, value * 2, output * 2)
        # Verify it doesn't double replace &.
        self.check_output(escape, "<&", "&lt;&amp;")