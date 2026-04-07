def test_invert(self):
        f = F("field")
        self.assertEqual(~f, NegatedExpression(f))
        self.assertIsNot(~~f, f)
        self.assertEqual(~~f, f)