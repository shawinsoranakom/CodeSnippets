def test_sitemaps_lastmod_ascending(self):
        """
        The Last-Modified header is set to the most recent sitemap lastmod.
        Test sitemaps are sorted by lastmod in ascending order.
        """
        response = self.client.get("/lastmod-sitemaps/ascending.xml")
        self.assertEqual(
            response.headers["Last-Modified"], "Sat, 20 Apr 2013 05:00:00 GMT"
        )