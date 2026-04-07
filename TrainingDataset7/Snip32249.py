def test_sitemap_get_latest_lastmod_none(self):
        """
        sitemapindex.lastmod is omitted when Sitemap.lastmod is
        callable and Sitemap.get_latest_lastmod is not implemented
        """
        response = self.client.get("/lastmod/get-latest-lastmod-none-sitemap.xml")
        self.assertNotContains(response, "<lastmod>")