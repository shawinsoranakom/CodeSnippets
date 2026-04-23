def test_basic_edit_GET(self):
        """
        A smoke test to ensure GET on the change_view works.
        """
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        )
        self.assertIsInstance(response, TemplateResponse)
        self.assertEqual(response.status_code, 200)