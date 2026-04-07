def test_deepcopy(self):
        d1 = MultiValueDict({"a": [[123]]})
        d2 = copy.copy(d1)
        d3 = copy.deepcopy(d1)
        self.assertIs(d1["a"], d2["a"])
        self.assertIsNot(d1["a"], d3["a"])