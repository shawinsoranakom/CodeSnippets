def _test_get_prep_value(self, f):
        self.assertIs(f.get_prep_value(True), True)
        self.assertIs(f.get_prep_value("1"), True)
        self.assertIs(f.get_prep_value(1), True)
        self.assertIs(f.get_prep_value(False), False)
        self.assertIs(f.get_prep_value("0"), False)
        self.assertIs(f.get_prep_value(0), False)
        self.assertIsNone(f.get_prep_value(None))