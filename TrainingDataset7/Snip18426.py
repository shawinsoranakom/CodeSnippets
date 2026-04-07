def test_user_with_unusable_password_change_password(self):
        # Test for title with unusable password with a test user
        test_user = User.objects.get(email="staffmember@example.com")
        test_user.set_unusable_password()
        test_user.save()
        user_change_url = reverse(
            "auth_test_admin:auth_user_change", args=(test_user.pk,)
        )
        password_change_url = reverse(
            "auth_test_admin:auth_user_password_change", args=(test_user.pk,)
        )

        response = self.client.get(user_change_url)
        # Test the link inside password field help_text.
        rel_link = re.search(
            r'<a role="button" class="button" href="([^"]*)">Set password</a>',
            response.text,
        )[1]
        self.assertEqual(urljoin(user_change_url, rel_link), password_change_url)

        response = self.client.get(password_change_url)
        # Test the form title with original (usable) password
        self.assertContains(response, f"<h1>Set password: {test_user.username}</h1>")
        # Breadcrumb.
        self.assertContains(
            response,
            f'{test_user.username}</a></li>\n<li aria-current="page">'
            "Set password</li>",
        )
        # Submit buttons
        self.assertContains(response, '<input type="submit" name="set-password"')
        self.assertNotContains(response, '<input type="submit" name="unset-password"')

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