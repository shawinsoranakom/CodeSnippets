def test_decode(self):
        """Semicolons and commas are decoded."""
        c = SimpleCookie()
        c["test"] = "An,awkward;value"
        c2 = SimpleCookie()
        c2.load(c.output()[12:])
        self.assertEqual(c["test"].value, c2["test"].value)
        c3 = parse_cookie(c.output()[12:])
        self.assertEqual(c["test"].value, c3["test"])