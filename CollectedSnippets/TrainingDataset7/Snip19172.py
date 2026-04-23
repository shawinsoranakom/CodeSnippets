def test_incr_decr_timeout(self):
        """
        incr/decr does not modify expiry time (matches memcached behavior)
        """
        key = "value"
        _key = cache.make_key(key)
        cache.set(key, 1, timeout=cache.default_timeout * 10)
        expire = cache._expire_info[_key]
        self.assertEqual(cache.incr(key), 2)
        self.assertEqual(expire, cache._expire_info[_key])
        self.assertEqual(cache.decr(key), 1)
        self.assertEqual(expire, cache._expire_info[_key])