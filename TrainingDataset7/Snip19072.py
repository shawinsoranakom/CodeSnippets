def test_decr(self):
        "Dummy cache values can't be decremented"
        cache.set("answer", 42)
        with self.assertRaises(ValueError):
            cache.decr("answer")
        with self.assertRaises(ValueError):
            cache.decr("does_not_exist")
        with self.assertRaises(ValueError):
            cache.decr("does_not_exist", -1)