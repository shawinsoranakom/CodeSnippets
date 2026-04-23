def test_get_regex(self):
        f = RegexField("^[a-z]+$")
        self.assertEqual(f.regex, re.compile("^[a-z]+$"))