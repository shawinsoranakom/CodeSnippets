def _perform_invalid_key_test(self, key, expected_warning):
        """
        While other backends merely warn, memcached should raise for an invalid
        key.
        """
        msg = expected_warning.replace(key, cache.make_key(key))
        tests = [
            ("add", [key, 1]),
            ("get", [key]),
            ("set", [key, 1]),
            ("incr", [key]),
            ("decr", [key]),
            ("touch", [key]),
            ("delete", [key]),
            ("get_many", [[key, "b"]]),
            ("set_many", [{key: 1, "b": 2}]),
            ("delete_many", [[key, "b"]]),
        ]
        for operation, args in tests:
            with self.subTest(operation=operation):
                with self.assertRaises(InvalidCacheKey) as cm:
                    getattr(cache, operation)(*args)
                self.assertEqual(str(cm.exception), msg)