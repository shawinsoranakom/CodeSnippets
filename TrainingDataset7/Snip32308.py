def test_clear_site_cache(self):
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "example.com",
            "SERVER_PORT": "80",
        }
        self.assertEqual(models.SITE_CACHE, {})
        get_current_site(request)
        expected_cache = {self.site.id: self.site}
        self.assertEqual(models.SITE_CACHE, expected_cache)

        with self.settings(SITE_ID=None):
            get_current_site(request)

        expected_cache.update({self.site.domain: self.site})
        self.assertEqual(models.SITE_CACHE, expected_cache)

        clear_site_cache(Site, instance=self.site, using="default")
        self.assertEqual(models.SITE_CACHE, {})