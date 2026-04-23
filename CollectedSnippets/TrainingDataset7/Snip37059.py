def test_prefix(self):
        self.assertEqual(static("test")[0].pattern.regex.pattern, "^test(?P<path>.*)$")