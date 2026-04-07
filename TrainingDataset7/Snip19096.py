def test_in(self):
        # The in operator can be used to inspect cache contents
        cache.set("hello2", "goodbye2")
        self.assertIn("hello2", cache)
        self.assertNotIn("goodbye2", cache)
        cache.set("null", None)
        self.assertIn("null", cache)