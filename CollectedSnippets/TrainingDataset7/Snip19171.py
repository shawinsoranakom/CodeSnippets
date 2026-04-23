def test_locking_on_pickle(self):
        """#20613/#18541 -- Ensures pickling is done outside of the lock."""
        bad_obj = PicklingSideEffect(cache)
        cache.set("set", bad_obj)
        self.assertFalse(bad_obj.locked, "Cache was locked during pickling")

        self.assertIs(cache.add("add", bad_obj), True)
        self.assertFalse(bad_obj.locked, "Cache was locked during pickling")