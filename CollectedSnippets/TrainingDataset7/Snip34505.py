def test_not(self):
        var = IfParser(["not", False]).parse()
        self.assertEqual("(not (literal False))", repr(var))
        self.assertTrue(var.eval({}))

        self.assertFalse(IfParser(["not", True]).parse().eval({}))