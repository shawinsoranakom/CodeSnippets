def test_mark_safe_str(self):
        """
        Calling str() on a SafeString instance doesn't lose the safe status.
        """
        s = mark_safe("a&b")
        self.assertIsInstance(str(s), type(s))