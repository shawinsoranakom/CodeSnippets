def test_secure_view_shows_login_if_not_logged_in(self):
        secure_url = reverse("secure_view")
        response = self.client.get(secure_url)
        self.assertRedirects(
            response, "%s?next=%s" % (reverse("admin:login"), secure_url)
        )
        response = self.client.get(secure_url, follow=True)
        self.assertTemplateUsed(response, "admin/login.html")
        self.assertEqual(response.context[REDIRECT_FIELD_NAME], secure_url)