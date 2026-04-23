def test_origin_compares_equal(self):
        a = self.engine.get_template("index.html")
        b = self.engine.get_template("index.html")
        self.assertEqual(a.origin, b.origin)
        # Use assertIs() to test __eq__/__ne__.
        self.assertIs(a.origin == b.origin, True)
        self.assertIs(a.origin != b.origin, False)