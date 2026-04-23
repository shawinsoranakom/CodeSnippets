def test_set_many_empty_data(self):
        self.assertEqual(cache.set_many({}), [])