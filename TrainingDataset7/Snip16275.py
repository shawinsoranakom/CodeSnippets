def test_basic_add_GET(self):
        """
        A smoke test to ensure GET on the add_view works.
        """
        response = self.client.get(reverse("admin:admin_views_section_add"))
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.status_code, 200)