def test_no_section(self):
        response = self.client.get("/simple/sitemap-simple2.xml")
        self.assertEqual(
            str(response.context["exception"]),
            "No sitemap available for section: 'simple2'",
        )
        self.assertEqual(response.status_code, 404)