def test_lt(self):
        obj1 = self.lazy_wrap(1)
        obj2 = self.lazy_wrap(2)
        self.assertLess(obj1, obj2)