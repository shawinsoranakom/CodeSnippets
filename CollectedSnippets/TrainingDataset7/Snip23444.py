def test_basic_add_GET(self):
        """
        A smoke test to ensure GET on the add_view works.
        """
        response = self.client.get(reverse("admin:generic_inline_admin_episode_add"))
        self.assertEqual(response.status_code, 200)