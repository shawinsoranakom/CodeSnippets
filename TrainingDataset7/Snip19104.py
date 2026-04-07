def test_expiration(self):
        # Cache values can be set to expire
        cache.set("expire1", "very quickly", 1)
        cache.set("expire2", "very quickly", 1)
        cache.set("expire3", "very quickly", 1)

        time.sleep(2)
        self.assertIsNone(cache.get("expire1"))

        self.assertIs(cache.add("expire2", "newvalue"), True)
        self.assertEqual(cache.get("expire2"), "newvalue")
        self.assertIs(cache.has_key("expire3"), False)