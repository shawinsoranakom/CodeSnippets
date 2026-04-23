def test_gt(self):
        obj1 = self.lazy_wrap(1)
        obj2 = self.lazy_wrap(2)
        self.assertGreater(obj2, obj1)