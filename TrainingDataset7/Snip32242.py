def test_sitemap_last_modified_tz(self):
        """
        The Last-Modified header should be converted from timezone aware dates
        to GMT.
        """
        response = self.client.get("/lastmod/tz-sitemap.xml")
        self.assertEqual(
            response.headers["Last-Modified"], "Wed, 13 Mar 2013 15:00:00 GMT"
        )