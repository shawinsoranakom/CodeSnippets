def test_encode(self):
        """Semicolons and commas are encoded."""
        c = SimpleCookie()
        c["test"] = "An,awkward;value"
        self.assertNotIn(";", c.output().rstrip(";"))  # IE compat
        self.assertNotIn(",", c.output().rstrip(";"))