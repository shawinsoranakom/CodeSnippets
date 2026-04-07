def test_lru_incr(self):
        """incr() moves cache keys."""
        for key in range(9):
            cache.set(key, key, timeout=None)
        for key in range(6):
            self.assertEqual(cache.incr(key), key + 1)
        cache.set(9, 9, timeout=None)
        for key in range(6):
            self.assertEqual(cache.get(key), key + 1)
        for key in range(6, 9):
            self.assertIsNone(cache.get(key))
        self.assertEqual(cache.get(9), 9)