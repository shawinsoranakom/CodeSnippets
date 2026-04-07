def test_empty_page(self):
        response = self.client.get("/simple/sitemap-simple.xml?p=0")
        self.assertEqual(str(response.context["exception"]), "Page 0 empty")
        self.assertEqual(response.status_code, 404)