def test_sitemap_get_latest_lastmod(self):
        """
        sitemapindex.lastmod is included when Sitemap.lastmod is
        attribute and Sitemap.get_latest_lastmod is implemented
        """
        response = self.client.get("/lastmod/get-latest-lastmod-sitemap.xml")
        self.assertContains(response, "<lastmod>2013-03-13T10:00:00</lastmod>")