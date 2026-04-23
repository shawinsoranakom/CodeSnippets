def test_origin_compares_not_equal(self):
        a = self.engine.get_template("first/test.html")
        b = self.engine.get_template("second/test.html")
        self.assertNotEqual(a.origin, b.origin)
        # Use assertIs() to test __eq__/__ne__.
        self.assertIs(a.origin == b.origin, False)
        self.assertIs(a.origin != b.origin, True)