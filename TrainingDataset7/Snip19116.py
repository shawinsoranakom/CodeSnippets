def test_forever_timeout(self):
        """
        Passing in None into timeout results in a value that is cached forever
        """
        cache.set("key1", "eggs", None)
        self.assertEqual(cache.get("key1"), "eggs")

        self.assertIs(cache.add("key2", "ham", None), True)
        self.assertEqual(cache.get("key2"), "ham")
        self.assertIs(cache.add("key1", "new eggs", None), False)
        self.assertEqual(cache.get("key1"), "eggs")

        cache.set_many({"key3": "sausage", "key4": "lobster bisque"}, None)
        self.assertEqual(cache.get("key3"), "sausage")
        self.assertEqual(cache.get("key4"), "lobster bisque")

        cache.set("key5", "belgian fries", timeout=1)
        self.assertIs(cache.touch("key5", timeout=None), True)
        time.sleep(2)
        self.assertEqual(cache.get("key5"), "belgian fries")