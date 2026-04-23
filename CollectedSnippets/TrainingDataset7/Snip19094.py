def test_delete_nonexistent(self):
        self.assertIs(cache.delete("nonexistent_key"), False)