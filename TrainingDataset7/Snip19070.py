def test_in(self):
        "The in operator doesn't ever return True for the dummy cache backend"
        cache.set("hello2", "goodbye2")
        self.assertNotIn("hello2", cache)
        self.assertNotIn("goodbye2", cache)