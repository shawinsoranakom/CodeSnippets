def test_force_str_lazy(self):
        s = SimpleLazyObject(lambda: "x")
        self.assertIs(type(force_str(s)), str)