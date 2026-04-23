def test_link_to_password_reset_in_user_change_form(self):
        cases = [
            (
                "testclient",
                "Raw passwords are not stored, so there is no way to see "
                "the user’s password.",
                "Reset password",
            ),
            (
                "unusable_password",
                "Enable password-based authentication for this user by setting a "
                "password.",
                "Set password",
            ),
        ]
        password_reset_link = (
            r'<a role="button" class="button" href="([^"]*)">([^<]*)</a>'
        )
        for username, expected_help_text, expected_button_label in cases:
            with self.subTest(username=username):
                user = User.objects.get(username=username)
                form = UserChangeForm(data={}, instance=user)
                password_help_text = form.fields["password"].help_text
                self.assertEqual(password_help_text, expected_help_text)

                matches = re.search(password_reset_link, form.as_p())
                self.assertIsNotNone(matches)
                self.assertEqual(len(matches.groups()), 2)
                url_prefix = f"admin:{user._meta.app_label}_{user._meta.model_name}"
                # URL to UserChangeForm in admin via to_field (instead of pk).
                user_change_url = reverse(f"{url_prefix}_change", args=(user.pk,))
                joined_url = urllib.parse.urljoin(user_change_url, matches.group(1))

                pw_change_url = reverse(
                    f"{url_prefix}_password_change", args=(user.pk,)
                )
                self.assertEqual(joined_url, pw_change_url)
                self.assertEqual(matches.group(2), expected_button_label)