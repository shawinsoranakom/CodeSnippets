def test_invalid_key_characters(self):
        # memcached doesn't allow whitespace or control characters in keys.
        key = "key with spaces and 清"
        self._perform_invalid_key_test(key, KEY_ERRORS_WITH_MEMCACHED_MSG % key)