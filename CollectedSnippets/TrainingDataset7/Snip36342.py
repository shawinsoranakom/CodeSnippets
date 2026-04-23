def test_lazy_mod_int(self):
        lazy_4 = lazy(lambda: 4, int)
        lazy_5 = lazy(lambda: 5, int)
        self.assertEqual(4 % lazy_5(), 4)
        self.assertEqual(lazy_4() % 5, 4)
        self.assertEqual(lazy_4() % lazy_5(), 4)