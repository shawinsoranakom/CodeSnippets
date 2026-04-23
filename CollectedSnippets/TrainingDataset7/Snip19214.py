def test_custom_key_validation(self):
        # this key is both longer than 250 characters, and has spaces
        key = "some key with spaces" * 15
        val = "a value"
        cache.set(key, val)
        self.assertEqual(cache.get(key), val)