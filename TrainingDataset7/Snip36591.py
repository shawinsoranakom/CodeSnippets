def setUp(self):
        super().setUp()
        sys.path_hooks.insert(0, TestFinder)
        sys.path_importer_cache.clear()