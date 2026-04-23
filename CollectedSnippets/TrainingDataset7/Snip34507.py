def test_in(self):
        list_ = [1, 2, 3]
        self.assertCalcEqual(True, [1, "in", list_])
        self.assertCalcEqual(False, [1, "in", None])
        self.assertCalcEqual(False, [None, "in", list_])