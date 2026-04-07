def test_escapejs(self):
        items = (
            (
                "\"double quotes\" and 'single quotes'",
                "\\u0022double quotes\\u0022 and \\u0027single quotes\\u0027",
            ),
            (r"\ : backslashes, too", "\\u005C : backslashes, too"),
            (
                "and lots of whitespace: \r\n\t\v\f\b",
                "and lots of whitespace: \\u000D\\u000A\\u0009\\u000B\\u000C\\u0008",
            ),
            (
                r"<script>and this</script>",
                "\\u003Cscript\\u003Eand this\\u003C/script\\u003E",
            ),
            (
                "paragraph separator:\u2029and line separator:\u2028",
                "paragraph separator:\\u2029and line separator:\\u2028",
            ),
            ("`", "\\u0060"),
            ("\u007f", "\\u007F"),
            ("\u0080", "\\u0080"),
            ("\u009f", "\\u009F"),
        )
        for value, output in items:
            with self.subTest(value=value, output=output):
                self.check_output(escapejs, value, output)
                self.check_output(escapejs, lazystr(value), output)