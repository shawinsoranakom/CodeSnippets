def setUp(self):
        django_file_prefixes.cache_clear()
        self.addCleanup(django_file_prefixes.cache_clear)