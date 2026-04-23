def test_callable_sitemod_no_items(self):
        index_response = self.client.get("/callable-lastmod-no-items/index.xml")
        self.assertNotIn("Last-Modified", index_response)
        expected_content_index = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap><loc>http://example.com/simple/sitemap-callable-lastmod.xml</loc></sitemap>
        </sitemapindex>
        """
        self.assertXMLEqual(index_response.text, expected_content_index)