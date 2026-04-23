def test_site_cache(self):
        # After updating a Site object (e.g. via the admin), we shouldn't
        # return a bogus value from the SITE_CACHE.
        site = Site.objects.get_current()
        self.assertEqual("example.com", site.name)
        s2 = Site.objects.get(id=settings.SITE_ID)
        s2.name = "Example site"
        s2.save()
        site = Site.objects.get_current()
        self.assertEqual("Example site", site.name)