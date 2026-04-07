def test_unknown_url_redirects_login_if_not_authenticated(self):
        unknown_url = "/test_admin/admin/unknown/"
        response = self.client.get(unknown_url)
        self.assertRedirects(
            response, "%s?next=%s" % (reverse("admin:login"), unknown_url)
        )