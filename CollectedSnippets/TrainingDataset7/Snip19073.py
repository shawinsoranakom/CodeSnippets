def test_touch(self):
        """Dummy cache can't do touch()."""
        self.assertIs(cache.touch("whatever"), False)