def test_generic_sitemap_lastmod(self):
        test_model = TestModel.objects.first()
        TestModel.objects.update(lastmod=datetime(2013, 3, 13, 10, 0, 0))
        response = self.client.get("/generic-lastmod/sitemap.xml")
        expected_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            "<url><loc>%s/testmodel/%s/</loc><lastmod>2013-03-13</lastmod></url>\n"
            "</urlset>"
        ) % (
            self.base_url,
            test_model.pk,
        )
        self.assertXMLEqual(response.text, expected_content)
        self.assertEqual(
            response.headers["Last-Modified"], "Wed, 13 Mar 2013 10:00:00 GMT"
        )