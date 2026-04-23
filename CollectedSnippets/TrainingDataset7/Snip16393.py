def test_custom_admin_site_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin2:my_view"))
        self.assertEqual(response.content, b"Django is a magical pony!")