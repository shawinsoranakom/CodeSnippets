def setUp(self):
        get_default_exception_reporter_filter.cache_clear()
        self.addCleanup(get_default_exception_reporter_filter.cache_clear)