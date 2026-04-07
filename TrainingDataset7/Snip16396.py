def test_login(self):
        """
        Make sure only staff members can log in.

        Successful posts to the login page will redirect to the original url.
        Unsuccessful attempts will continue to render the login page with
        a 200 status code.
        """
        login_url = "%s?next=%s" % (reverse("admin:login"), reverse("admin:index"))
        # Super User
        response = self.client.get(self.index_url)
        self.assertRedirects(response, login_url)
        login = self.client.post(login_url, self.super_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)
        self.client.post(reverse("admin:logout"))

        # Test if user enters email address
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.super_email_login)
        self.assertContains(login, ERROR_MESSAGE)
        # only correct passwords get a username hint
        login = self.client.post(login_url, self.super_email_bad_login)
        self.assertContains(login, ERROR_MESSAGE)
        new_user = User(username="jondoe", password="secret", email="super@example.com")
        new_user.save()
        # check to ensure if there are multiple email addresses a user doesn't
        # get a 500
        login = self.client.post(login_url, self.super_email_login)
        self.assertContains(login, ERROR_MESSAGE)

        # View User
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.viewuser_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)
        self.client.post(reverse("admin:logout"))

        # Add User
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.adduser_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)
        self.client.post(reverse("admin:logout"))

        # Change User
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.changeuser_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)
        self.client.post(reverse("admin:logout"))

        # Delete User
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.deleteuser_login)
        self.assertRedirects(login, self.index_url)
        self.assertFalse(login.context)
        self.client.post(reverse("admin:logout"))

        # Regular User should not be able to login.
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.joepublic_login)
        self.assertContains(login, ERROR_MESSAGE)

        # Requests without username should not return 500 errors.
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 302)
        login = self.client.post(login_url, self.no_username_login)
        self.assertEqual(login.status_code, 200)
        self.assertFormError(
            login.context["form"], "username", ["This field is required."]
        )