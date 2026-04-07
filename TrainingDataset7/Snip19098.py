def test_decr(self):
        # Cache values can be decremented
        cache.set("answer", 43)
        self.assertEqual(cache.decr("answer"), 42)
        self.assertEqual(cache.get("answer"), 42)
        self.assertEqual(cache.decr("answer", 10), 32)
        self.assertEqual(cache.get("answer"), 32)
        self.assertEqual(cache.decr("answer", -10), 42)
        with self.assertRaises(ValueError):
            cache.decr("does_not_exist")
        with self.assertRaises(ValueError):
            cache.incr("does_not_exist", -1)
        cache.set("null", None)
        with self.assertRaises(self.incr_decr_type_error):
            cache.decr("null")