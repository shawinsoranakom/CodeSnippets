def test_missing_slash_append_slash_true_unknown_url(self):
        self.client.force_login(self.staff_user)
        unknown_url = "/test_admin/admin/unknown/"
        response = self.client.get(unknown_url[:-1])
        self.assertEqual(response.status_code, 404)