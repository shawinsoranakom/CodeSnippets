def test_basic_edit_POST(self):
        """
        A smoke test to ensure POST on edit_view works.
        """
        url = reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        response = self.client.post(url, self.inline_post_data)
        self.assertEqual(response.status_code, 302)