def test_sitemap_get_urls_no_site_1(self):
        """
        Check we get ImproperlyConfigured if we don't pass a site object to
        Sitemap.get_urls and no Site objects exist
        """
        Site.objects.all().delete()
        with self.assertRaisesMessage(ImproperlyConfigured, self.use_sitemap_err_msg):
            Sitemap().get_urls()