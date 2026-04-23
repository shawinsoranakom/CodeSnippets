def test_zero_timeout(self):
        """
        Passing in zero into timeout results in a value that is not cached
        """
        cache.set("key1", "eggs", 0)
        self.assertIsNone(cache.get("key1"))

        self.assertIs(cache.add("key2", "ham", 0), True)
        self.assertIsNone(cache.get("key2"))

        cache.set_many({"key3": "sausage", "key4": "lobster bisque"}, 0)
        self.assertIsNone(cache.get("key3"))
        self.assertIsNone(cache.get("key4"))

        cache.set("key5", "belgian fries", timeout=5)
        self.assertIs(cache.touch("key5", timeout=0), True)
        self.assertIsNone(cache.get("key5"))