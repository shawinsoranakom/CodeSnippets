def test_sitemap_get_urls_no_site_2(self):
        """
        Check we get ImproperlyConfigured when we don't pass a site object to
        Sitemap.get_urls if Site objects exists, but the sites framework is not
        actually installed.
        """
        with self.assertRaisesMessage(ImproperlyConfigured, self.use_sitemap_err_msg):
            Sitemap().get_urls()