def test_delete_many_no_keys(self):
        self.assertIsNone(cache.delete_many([]))