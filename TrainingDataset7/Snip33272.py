def test_invalid_value(self):
        self.assertIs(yesno(True, "yes"), True)
        self.assertIs(yesno(False, "yes"), False)
        self.assertIsNone(yesno(None, "yes"))