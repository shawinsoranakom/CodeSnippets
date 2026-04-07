def test_GET_parent_add(self):
        """
        InlineModelAdmin broken?
        """
        response = self.client.get(reverse("admin:admin_views_parent_add"))
        self.assertEqual(response.status_code, 200)