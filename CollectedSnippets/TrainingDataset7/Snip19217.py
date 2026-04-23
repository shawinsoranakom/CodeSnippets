def setUp(self):
        # The 5 minute (300 seconds) default expiration time for keys is
        # defined in the implementation of the initializer method of the
        # BaseCache type.
        self.DEFAULT_TIMEOUT = caches[DEFAULT_CACHE_ALIAS].default_timeout