def test_non_admin_url_404_if_not_authenticated(self):
        unknown_url = "/unknown/"
        response = self.client.get(unknown_url)
        # Does not redirect to the admin login.
        self.assertEqual(response.status_code, 404)