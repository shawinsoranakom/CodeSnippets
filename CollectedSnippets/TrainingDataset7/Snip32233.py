def test_simple_sitemap_custom_lastmod_index(self):
        "A simple sitemap index can be rendered with a custom template"
        response = self.client.get("/simple/custom-lastmod-index.xml")
        expected_content = """<?xml version="1.0" encoding="UTF-8"?>
<!-- This is a customized template -->
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>%s/simple/sitemap-simple.xml</loc><lastmod>%s</lastmod></sitemap>
</sitemapindex>
""" % (
            self.base_url,
            date.today(),
        )
        self.assertXMLEqual(response.text, expected_content)