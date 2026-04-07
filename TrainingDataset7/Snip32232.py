def test_paged_sitemap(self):
        """A sitemap may have multiple pages."""
        response = self.client.get("/simple-paged/index.xml")
        expected_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>{0}/simple/sitemap-simple.xml</loc><lastmod>{1}</lastmod></sitemap><sitemap><loc>{0}/simple/sitemap-simple.xml?p=2</loc><lastmod>{1}</lastmod></sitemap>
</sitemapindex>
""".format(self.base_url, date.today())
        self.assertXMLEqual(response.text, expected_content)