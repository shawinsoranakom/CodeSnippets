def test_login_redirect_for_direct_get(self):
        """
        Login redirect should be to the admin index page when going directly to
        /admin/login/.
        """
        response = self.client.get(reverse("admin:login"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[REDIRECT_FIELD_NAME], reverse("admin:index"))