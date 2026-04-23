def test_set_many_returns_empty_list_on_success(self):
        """set_many() returns an empty list when all keys are inserted."""
        failing_keys = cache.set_many({"key1": "spam", "key2": "eggs"})
        self.assertEqual(failing_keys, [])