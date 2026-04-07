def test_double_login_is_not_allowed(self):
        """Regression test for #19327"""
        login_url = "%s?next=%s" % (reverse("admin:login"), reverse("admin:index"))

        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)

        # Establish a valid admin session
        login = self.client.post(login_url, self.super_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)

        # Logging in with non-admin user fails
        login = self.client.post(login_url, self.joepublic_login)
        self.assertContains(login, ERROR_MESSAGE)

        # Establish a valid admin session
        login = self.client.post(login_url, self.super_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)

        # Logging in with admin user while already logged in
        login = self.client.post(login_url, self.super_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)
        self.client.post(reverse("admin:logout"))