def test_expiration(self):
        "Expiration has no effect on the dummy cache"
        cache.set("expire1", "very quickly", 1)
        cache.set("expire2", "very quickly", 1)
        cache.set("expire3", "very quickly", 1)

        time.sleep(2)
        self.assertIsNone(cache.get("expire1"))

        self.assertIs(cache.add("expire2", "newvalue"), True)
        self.assertIsNone(cache.get("expire2"))
        self.assertIs(cache.has_key("expire3"), False)