def test_cache(self):
        finders.get_finder.cache_clear()
        for n in range(10):
            finders.get_finder("django.contrib.staticfiles.finders.FileSystemFinder")
        cache_info = finders.get_finder.cache_info()
        self.assertEqual(cache_info.hits, 9)
        self.assertEqual(cache_info.currsize, 1)