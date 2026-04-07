def test_clear_site_cache_domain(self):
        site = Site.objects.create(name="example2.com", domain="example2.com")
        request = HttpRequest()
        request.META = {
            "SERVER_NAME": "example2.com",
            "SERVER_PORT": "80",
        }
        get_current_site(request)  # prime the models.SITE_CACHE
        expected_cache = {site.domain: site}
        self.assertEqual(models.SITE_CACHE, expected_cache)

        # Site exists in 'default' database so using='other' shouldn't clear.
        clear_site_cache(Site, instance=site, using="other")
        self.assertEqual(models.SITE_CACHE, expected_cache)
        # using='default' should clear.
        clear_site_cache(Site, instance=site, using="default")
        self.assertEqual(models.SITE_CACHE, {})