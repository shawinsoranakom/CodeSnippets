def assertCalcEqual(self, expected, tokens):
        self.assertEqual(expected, IfParser(tokens).parse().eval({}))