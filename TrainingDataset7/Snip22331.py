def test_flatpage_sitemap(self):
        response = self.client.get("/flatpages/sitemap.xml")
        self.assertIn(
            b"<url><loc>http://example.com/flatpage_root/foo/</loc></url>",
            response.getvalue(),
        )
        self.assertNotIn(
            b"<url><loc>http://example.com/flatpage_root/private-foo/</loc></url>",
            response.getvalue(),
        )