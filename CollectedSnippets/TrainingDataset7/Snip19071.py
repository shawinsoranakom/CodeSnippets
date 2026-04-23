def test_incr(self):
        "Dummy cache values can't be incremented"
        cache.set("answer", 42)
        with self.assertRaises(ValueError):
            cache.incr("answer")
        with self.assertRaises(ValueError):
            cache.incr("does_not_exist")
        with self.assertRaises(ValueError):
            cache.incr("does_not_exist", -1)