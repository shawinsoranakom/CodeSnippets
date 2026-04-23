def setUp(self):
        # Make sure the cache is empty before we are doing our tests.
        clear_url_caches()
        # Make sure we will leave an empty cache for other testcases.
        self.addCleanup(clear_url_caches)