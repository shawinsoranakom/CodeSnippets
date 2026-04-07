def test_lazy_string(self):
        append_script = lazy(lambda string: r"<script>this</script>" + string, str)
        self.assertEqual(
            escapejs_filter(append_script("whitespace: \r\n\t\v\f\b")),
            "\\u003Cscript\\u003Ethis\\u003C/script\\u003E"
            "whitespace: \\u000D\\u000A\\u0009\\u000B\\u000C\\u0008",
        )