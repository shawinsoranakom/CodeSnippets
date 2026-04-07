def test_long_timeout(self):
        """
        Follow memcached's convention where a timeout greater than 30 days is
        treated as an absolute expiration timestamp instead of a relative
        offset (#12399).
        """
        cache.set("key1", "eggs", 60 * 60 * 24 * 30 + 1)  # 30 days + 1 second
        self.assertEqual(cache.get("key1"), "eggs")

        self.assertIs(cache.add("key2", "ham", 60 * 60 * 24 * 30 + 1), True)
        self.assertEqual(cache.get("key2"), "ham")

        cache.set_many(
            {"key3": "sausage", "key4": "lobster bisque"}, 60 * 60 * 24 * 30 + 1
        )
        self.assertEqual(cache.get("key3"), "sausage")
        self.assertEqual(cache.get("key4"), "lobster bisque")