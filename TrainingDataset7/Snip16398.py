def test_login_redirect_when_logged_in(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:login"))
        self.assertRedirects(response, reverse("admin:index"))