def test_empty_cache_file_considered_expired(self):
        cache_file = cache._key_to_file("foo")
        with open(cache_file, "wb") as fh:
            fh.write(b"")
        with open(cache_file, "rb") as fh:
            self.assertIs(cache._is_expired(fh), True)