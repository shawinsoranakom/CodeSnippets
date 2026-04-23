def test_decr_version(self):
        "Dummy cache versions can't be decremented"
        cache.set("answer", 42)
        with self.assertRaises(ValueError):
            cache.decr_version("answer")
        with self.assertRaises(ValueError):
            cache.decr_version("does_not_exist")