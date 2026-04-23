def test_sitemap_index_with_https_request(self):
        "A sitemap index requested in HTTPS is rendered with HTTPS links"
        response = self.client.get("/simple/index.xml", **self.extra)
        expected_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>%s/simple/sitemap-simple.xml</loc><lastmod>%s</lastmod></sitemap>
</sitemapindex>
""" % (
            self.base_url.replace("http://", "https://"),
            date.today(),
        )
        self.assertXMLEqual(response.text, expected_content)