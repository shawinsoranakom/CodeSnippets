def test_same_instance(self):
        """
        Attempting to retrieve the same alias should yield the same instance.
        """
        cache1 = caches["default"]
        cache2 = caches["default"]

        self.assertIs(cache1, cache2)