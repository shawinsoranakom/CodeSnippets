def test_regexfield_strip(self):
        f = RegexField("^[a-z]+$", strip=True)
        self.assertEqual(f.clean(" a"), "a")
        self.assertEqual(f.clean("a "), "a")