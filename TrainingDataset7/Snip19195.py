def test_creates_cache_dir_if_nonexistent(self):
        os.rmdir(self.dirname)
        cache.set("foo", "bar")
        self.assertTrue(os.path.exists(self.dirname))