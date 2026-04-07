def test_unknown_url_404_if_authenticated(self):
        self.client.force_login(self.staff_user)
        unknown_url = "/test_admin/admin/unknown/"
        response = self.client.get(unknown_url)
        self.assertEqual(response.status_code, 404)