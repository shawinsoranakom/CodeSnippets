def test_lru_set(self):
        """set() moves cache keys."""
        for key in range(9):
            cache.set(key, key, timeout=None)
        for key in range(3, 9):
            cache.set(key, key, timeout=None)
        cache.set(9, 9, timeout=None)
        for key in range(3, 10):
            self.assertEqual(cache.get(key), key)
        for key in range(3):
            self.assertIsNone(cache.get(key))