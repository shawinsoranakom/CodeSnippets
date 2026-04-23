def test_has_key(self):
        """
        The has_key method doesn't ever return True for the dummy cache backend
        """
        cache.set("hello1", "goodbye1")
        self.assertIs(cache.has_key("hello1"), False)
        self.assertIs(cache.has_key("goodbye1"), False)