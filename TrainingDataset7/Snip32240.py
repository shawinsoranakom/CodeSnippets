def test_sitemap_last_modified(self):
        "Last-Modified header is set correctly"
        response = self.client.get("/lastmod/sitemap.xml")
        self.assertEqual(
            response.headers["Last-Modified"], "Wed, 13 Mar 2013 10:00:00 GMT"
        )