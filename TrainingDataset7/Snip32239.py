def test_simple_custom_sitemap(self):
        "A simple sitemap can be rendered with a custom template"
        response = self.client.get("/simple/custom-sitemap.xml")
        expected_content = """<?xml version="1.0" encoding="UTF-8"?>
<!-- This is a customized template -->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>%s/location/</loc><lastmod>%s</lastmod><changefreq>never</changefreq><priority>0.5</priority></url>
</urlset>
""" % (
            self.base_url,
            date.today(),
        )
        self.assertXMLEqual(response.text, expected_content)