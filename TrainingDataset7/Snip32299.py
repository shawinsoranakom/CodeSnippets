def setUp(self):
        Site.objects.clear_cache()
        self.addCleanup(Site.objects.clear_cache)