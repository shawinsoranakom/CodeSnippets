def test_sitemap_latest_lastmod_timezone(self):
        """
        lastmod datestamp shows timezones if Sitemap.get_latest_lastmod
        returns an aware datetime.
        """
        response = self.client.get("/lastmod/latest-lastmod-timezone-sitemap.xml")
        self.assertContains(response, "<lastmod>2013-03-13T10:00:00-05:00</lastmod>")