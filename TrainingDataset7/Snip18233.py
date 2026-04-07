def test_password_reset_confirm_view_error_form(self):
        client = PasswordResetConfirmClient()
        default_token_generator = PasswordResetTokenGenerator()
        token = default_token_generator.make_token(self.user)
        uidb64 = urlsafe_base64_encode(str(self.user.pk).encode())
        url = reverse(
            "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        response = client.post(url, {})
        self.assertContains(
            response,
            '<div class="flex-container errors">'
            '<label for="id_new_password1">New password:</label>'
            '<ul class="errorlist" id="id_new_password1_error">'
            "<li>This field is required.</li></ul>"
            '<input type="password" name="new_password1" autocomplete="new-password" '
            'required aria-invalid="true" aria-describedby="id_new_password1_error" '
            'id="id_new_password1"></div>',
            html=True,
        )
        self.assertContains(
            response,
            '<div class="flex-container errors">'
            '<label for="id_new_password2">Confirm password:</label>'
            '<ul class="errorlist" id="id_new_password2_error">'
            "<li>This field is required.</li></ul>"
            '<input type="password" name="new_password2" autocomplete="new-password" '
            'required aria-invalid="true" aria-describedby="id_new_password2_helptext '
            'id_new_password2_error" id="id_new_password2"></div>',
            html=True,
        )