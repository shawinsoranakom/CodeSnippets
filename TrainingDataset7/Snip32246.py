def test_sitemaps_lastmod_mixed_descending_last_modified_missing(self):
        """
        The Last-Modified header is omitted when lastmod isn't found in all
        sitemaps. Test sitemaps are sorted by lastmod in descending order.
        """
        response = self.client.get("/lastmod-sitemaps/mixed-descending.xml")
        self.assertFalse(response.has_header("Last-Modified"))