def test_lazy_add_list(self):
        lazy_4 = lazy(lambda: [4], list)
        lazy_5 = lazy(lambda: [5], list)
        self.assertEqual([4] + lazy_5(), [4, 5])
        self.assertEqual(lazy_4() + [5], [4, 5])
        self.assertEqual(lazy_4() + lazy_5(), [4, 5])