def test_ignores_non_cache_files(self):
        fname = os.path.join(self.dirname, "not-a-cache-file")
        with open(fname, "w"):
            os.utime(fname, None)
        cache.clear()
        self.assertTrue(
            os.path.exists(fname), "Expected cache.clear to ignore non cache files"
        )
        os.remove(fname)