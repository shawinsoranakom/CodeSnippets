def test_touch(self):
        # cache.touch() updates the timeout.
        cache.set("expire1", "very quickly", timeout=1)
        self.assertIs(cache.touch("expire1", timeout=4), True)
        time.sleep(2)
        self.assertIs(cache.has_key("expire1"), True)
        time.sleep(3)
        self.assertIs(cache.has_key("expire1"), False)
        # cache.touch() works without the timeout argument.
        cache.set("expire1", "very quickly", timeout=1)
        self.assertIs(cache.touch("expire1"), True)
        time.sleep(2)
        self.assertIs(cache.has_key("expire1"), True)

        self.assertIs(cache.touch("nonexistent"), False)