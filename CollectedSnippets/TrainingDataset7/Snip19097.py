def test_incr(self):
        # Cache values can be incremented
        cache.set("answer", 41)
        self.assertEqual(cache.incr("answer"), 42)
        self.assertEqual(cache.get("answer"), 42)
        self.assertEqual(cache.incr("answer", 10), 52)
        self.assertEqual(cache.get("answer"), 52)
        self.assertEqual(cache.incr("answer", -10), 42)
        with self.assertRaises(ValueError):
            cache.incr("does_not_exist")
        with self.assertRaises(ValueError):
            cache.incr("does_not_exist", -1)
        cache.set("null", None)
        with self.assertRaises(self.incr_decr_type_error):
            cache.incr("null")