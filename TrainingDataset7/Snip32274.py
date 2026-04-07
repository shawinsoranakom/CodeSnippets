def test_sitemap_section_with_https_request(self):
        "A sitemap section requested in HTTPS is rendered with HTTPS links"
        response = self.client.get("/simple/sitemap-simple.xml", **self.extra)
        expected_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            "<url><loc>%s/location/</loc><lastmod>%s</lastmod>"
            "<changefreq>never</changefreq><priority>0.5</priority></url>\n"
            "</urlset>"
        ) % (
            self.base_url.replace("http://", "https://"),
            date.today(),
        )
        self.assertXMLEqual(response.text, expected_content)