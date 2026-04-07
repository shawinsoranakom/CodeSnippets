def test_invalid_with_version_key_length(self):
        # Custom make_key() that adds a version to the key and exceeds the
        # limit.
        def key_func(key, *args):
            return key + ":1"

        key = "a" * 249
        expected_warning = (
            "Cache key will cause errors if used with memcached: "
            "%r (longer than %s)" % (key_func(key), 250)
        )
        self._perform_invalid_key_test(key, expected_warning, key_func=key_func)