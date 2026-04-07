def test_basic_add_GET(self):
        """
        Ensure GET on the add_view works.
        """
        add_url = reverse("admin_custom_urls:admin_custom_urls_action_add")
        self.assertTrue(add_url.endswith("/!add/"))
        response = self.client.get(add_url)
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.status_code, 200)