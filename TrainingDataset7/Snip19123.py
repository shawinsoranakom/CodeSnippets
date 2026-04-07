def _perform_invalid_key_test(self, key, expected_warning, key_func=None):
        """
        All the builtin backends should warn (except memcached that should
        error) on keys that would be refused by memcached. This encourages
        portable caching code without making it too difficult to use production
        backends with more liberal key rules. Refs #6447.
        """

        # mimic custom ``make_key`` method being defined since the default will
        # never show the below warnings
        def func(key, *args):
            return key

        old_func = cache.key_func
        cache.key_func = key_func or func

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
        try:
            for operation, args in tests:
                with self.subTest(operation=operation):
                    with self.assertWarns(CacheKeyWarning) as cm:
                        getattr(cache, operation)(*args)
                    self.assertEqual(str(cm.warning), expected_warning)
        finally:
            cache.key_func = old_func