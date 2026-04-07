def test_requestsite_sitemap(self):
        # Hitting the flatpages sitemap without the sites framework installed
        # doesn't raise an exception.
        response = self.client.get("/simple/sitemap.xml")
        expected_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            "<url><loc>http://testserver/location/</loc><lastmod>%s</lastmod>"
            "<changefreq>never</changefreq><priority>0.5</priority></url>\n"
            "</urlset>"
        ) % date.today()
        self.assertXMLEqual(response.text, expected_content)