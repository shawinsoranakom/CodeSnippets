def test_user_with_usable_password_change_password(self):
        user_change_url = reverse(
            "auth_test_admin:auth_user_change", args=(self.admin.pk,)
        )
        password_change_url = reverse(
            "auth_test_admin:auth_user_password_change", args=(self.admin.pk,)
        )

        response = self.client.get(user_change_url)
        # Test the link inside password field help_text.
        rel_link = re.search(
            r'<a role="button" class="button" href="([^"]*)">Reset password</a>',
            response.text,
        )[1]
        self.assertEqual(urljoin(user_change_url, rel_link), password_change_url)

        response = self.client.get(password_change_url)
        # Test the form title with original (usable) password
        self.assertContains(
            response, f"<h1>Change password: {self.admin.username}</h1>"
        )
        # Breadcrumb.
        self.assertContains(
            response,
            f'{self.admin.username}</a></li>\n<li aria-current="page">'
            "Change password</li>",
        )
        # Usable password field.
        self.assertContains(
            response,
            '<fieldset class="flex-container">'
            "<legend>Password-based authentication:</legend>",
        )
        # Submit buttons
        self.assertContains(response, '<input type="submit" name="set-password"')
        self.assertContains(response, '<input type="submit" name="unset-password"')

        # Password change.
        response = self.client.post(
            password_change_url,
            {
                "password1": "password1",
                "password2": "password1",
            },
        )
        self.assertRedirects(response, user_change_url)
        self.assertMessages(
            response, [Message(level=25, message="Password changed successfully.")]
        )
        row = LogEntry.objects.latest("id")
        self.assertEqual(row.get_change_message(), "Changed password.")
        self.logout()
        self.login(password="password1")

        # Disable password-based authentication without proper submit button.
        response = self.client.post(
            password_change_url,
            {
                "password1": "password1",
                "password2": "password1",
                "usable_password": "false",
            },
        )
        self.assertRedirects(response, password_change_url)
        self.assertMessages(
            response,
            [
                Message(
                    level=40,
                    message="Conflicting form data submitted. Please try again.",
                )
            ],
        )
        # No password change yet.
        self.login(password="password1")

        # Disable password-based authentication with proper submit button.
        response = self.client.post(
            password_change_url,
            {
                "password1": "password1",
                "password2": "password1",
                "usable_password": "false",
                "unset-password": 1,
            },
        )
        self.assertRedirects(response, user_change_url)
        self.assertMessages(
            response,
            [Message(level=25, message="Password-based authentication was disabled.")],
        )
        row = LogEntry.objects.latest("id")
        self.assertEqual(row.get_change_message(), "Changed password.")
        self.logout()
        # Password-based authentication was disabled.
        with self.assertRaises(AssertionError):
            self.login(password="password1")
        self.admin.refresh_from_db()
        self.assertIs(self.admin.has_usable_password(), False)