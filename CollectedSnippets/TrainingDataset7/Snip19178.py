def test_invalid_with_version_key_length(self):
        # make_key() adds a version to the key and exceeds the limit.
        key = "a" * 248
        expected_warning = (
            "Cache key will cause errors if used with memcached: "
            "%r (longer than %s)" % (key, 250)
        )
        self._perform_invalid_key_test(key, expected_warning)