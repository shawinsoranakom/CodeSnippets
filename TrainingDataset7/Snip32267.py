def test_callable_sitemod_partial(self):
        """
        Not all items have `lastmod`. Therefore the `Last-Modified` header
        is not set by the detail or index sitemap view.
        """
        index_response = self.client.get("/callable-lastmod-partial/index.xml")
        sitemap_response = self.client.get("/callable-lastmod-partial/sitemap.xml")
        self.assertNotIn("Last-Modified", index_response)
        self.assertNotIn("Last-Modified", sitemap_response)
        expected_content_index = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap><loc>http://example.com/simple/sitemap-callable-lastmod.xml</loc></sitemap>
        </sitemapindex>
        """
        expected_content_sitemap = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            "<url><loc>http://example.com/location/</loc>"
            "<lastmod>2013-03-13</lastmod></url><url>"
            "<loc>http://example.com/location/</loc></url>\n"
            "</urlset>"
        )
        self.assertXMLEqual(index_response.text, expected_content_index)
        self.assertXMLEqual(sitemap_response.text, expected_content_sitemap)