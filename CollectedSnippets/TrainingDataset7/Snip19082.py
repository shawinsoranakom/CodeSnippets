def test_incr_version(self):
        "Dummy cache versions can't be incremented"
        cache.set("answer", 42)
        with self.assertRaises(ValueError):
            cache.incr_version("answer")
        with self.assertRaises(ValueError):
            cache.incr_version("does_not_exist")