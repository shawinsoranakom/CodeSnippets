def test_cached_sitemap_index(self):
        """
        A cached sitemap index can be rendered (#2713).
        """
        response = self.client.get("/cached/index.xml")
        expected_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>%s/cached/sitemap-simple.xml</loc><lastmod>%s</lastmod></sitemap>
</sitemapindex>
""" % (
            self.base_url,
            date.today(),
        )
        self.assertXMLEqual(response.text, expected_content)