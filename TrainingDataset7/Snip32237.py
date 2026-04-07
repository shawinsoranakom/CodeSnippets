def test_page_not_int(self):
        response = self.client.get("/simple/sitemap-simple.xml?p=test")
        self.assertEqual(str(response.context["exception"]), "No page 'test'")
        self.assertEqual(response.status_code, 404)