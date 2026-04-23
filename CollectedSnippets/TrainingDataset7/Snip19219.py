def test_default_expiration_time_for_keys_is_5_minutes(self):
        """The default expiration time of a cache key is 5 minutes.

        This value is defined in
        django.core.cache.backends.base.BaseCache.__init__().
        """
        self.assertEqual(300, self.DEFAULT_TIMEOUT)