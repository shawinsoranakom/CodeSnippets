def test_sitemap_last_modified_mixed(self):
        "Last-Modified header is omitted when lastmod not on all items"
        response = self.client.get("/lastmod-mixed/sitemap.xml")
        self.assertFalse(response.has_header("Last-Modified"))