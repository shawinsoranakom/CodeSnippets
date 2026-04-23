def test_list_set(self):
        lazy_list = SimpleLazyObject(lambda: [1, 2, 3, 4, 5])
        lazy_set = SimpleLazyObject(lambda: {1, 2, 3, 4})
        self.assertIn(1, lazy_list)
        self.assertIn(1, lazy_set)
        self.assertNotIn(6, lazy_list)
        self.assertNotIn(6, lazy_set)
        self.assertEqual(len(lazy_list), 5)
        self.assertEqual(len(lazy_set), 4)