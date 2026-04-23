def test_empty_sitemap(self):
        response = self.client.get("/empty/sitemap.xml")
        self.assertEqual(response.status_code, 200)