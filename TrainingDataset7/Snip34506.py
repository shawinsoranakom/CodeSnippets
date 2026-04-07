def test_or(self):
        var = IfParser([True, "or", False]).parse()
        self.assertEqual("(or (literal True) (literal False))", repr(var))
        self.assertTrue(var.eval({}))