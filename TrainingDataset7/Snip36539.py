def test_radd(self):
        obj1 = self.lazy_wrap(1)
        self.assertEqual(1 + obj1, 2)