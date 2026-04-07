def test_password_reset_confirm_view_custom_username_hint(self):
        custom_user = CustomUser.custom_objects.create_user(
            email="joe@example.com",
            date_of_birth=date(1986, 11, 11),
            first_name="Joe",
        )
        client = PasswordResetConfirmClient()
        default_token_generator = PasswordResetTokenGenerator()
        token = default_token_generator.make_token(custom_user)
        uidb64 = urlsafe_base64_encode(str(custom_user.pk).encode())
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response = client.get(url)
        self.assertContains(
            response,
            "<title>Enter new password | Django site admin</title>",
        )
        self.assertContains(response, "<h1>Enter new password</h1>")
        # The username field is added to the password reset confirmation form
        # to help browser's password managers.
        self.assertContains(
            response,
            '<input class="hidden" autocomplete="username" value="joe@example.com">',
        )