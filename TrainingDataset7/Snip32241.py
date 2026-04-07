def test_sitemap_last_modified_date(self):
        """
        The Last-Modified header should be support dates (without time).
        """
        response = self.client.get("/lastmod/date-sitemap.xml")
        self.assertEqual(
            response.headers["Last-Modified"], "Wed, 13 Mar 2013 00:00:00 GMT"
        )