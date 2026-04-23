def test_charfield_strip(self):
        """
        Values have whitespace stripped but not if strip=False.
        """
        f = CharField()
        self.assertEqual(f.clean(" 1"), "1")
        self.assertEqual(f.clean("1 "), "1")

        f = CharField(strip=False)
        self.assertEqual(f.clean(" 1"), " 1")
        self.assertEqual(f.clean("1 "), "1 ")