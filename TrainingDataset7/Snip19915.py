def setUp(self):
        ContentType.objects.clear_cache()
        self.addCleanup(ContentType.objects.clear_cache)