def test_sitemap_last_modified_missing(self):
        "Last-Modified header is missing when sitemap has no lastmod"
        response = self.client.get("/generic/sitemap.xml")
        self.assertFalse(response.has_header("Last-Modified"))