def test_lru_get(self):
        """get() moves cache keys."""
        for key in range(9):
            cache.set(key, key, timeout=None)
        for key in range(6):
            self.assertEqual(cache.get(key), key)
        cache.set(9, 9, timeout=None)
        for key in range(6):
            self.assertEqual(cache.get(key), key)
        for key in range(6, 9):
            self.assertIsNone(cache.get(key))
        self.assertEqual(cache.get(9), 9)