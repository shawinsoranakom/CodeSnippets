def test_add(self):
        obj1 = self.lazy_wrap(1)
        self.assertEqual(obj1 + 1, 2)
        obj2 = self.lazy_wrap(2)
        self.assertEqual(obj2 + obj1, 3)
        self.assertEqual(obj1 + obj2, 3)