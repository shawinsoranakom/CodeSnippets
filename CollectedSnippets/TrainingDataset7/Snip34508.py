def test_not_in(self):
        list_ = [1, 2, 3]
        self.assertCalcEqual(False, [1, "not", "in", list_])
        self.assertCalcEqual(True, [4, "not", "in", list_])
        self.assertCalcEqual(False, [1, "not", "in", None])
        self.assertCalcEqual(True, [None, "not", "in", list_])