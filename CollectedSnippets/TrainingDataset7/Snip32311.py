def test_site_natural_key(self):
        self.assertEqual(Site.objects.get_by_natural_key(self.site.domain), self.site)
        self.assertEqual(self.site.natural_key(), (self.site.domain,))