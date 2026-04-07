def test_generic_sitemap_index(self):
        TestModel.objects.update(lastmod=datetime(2013, 3, 13, 10, 0, 0))
        response = self.client.get("/generic-lastmod/index.xml")
        expected_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>http://example.com/simple/sitemap-generic.xml</loc><lastmod>2013-03-13T10:00:00</lastmod></sitemap>
</sitemapindex>"""
        self.assertXMLEqual(response.text, expected_content)