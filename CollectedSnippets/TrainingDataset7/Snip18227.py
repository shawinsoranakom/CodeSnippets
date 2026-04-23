def test_password_reset_view_error_form(self):
        response = self.client.post(reverse("password_reset"), {})
        self.assertContains(
            response,
            '<div class="flex-container">'
            '<label for="id_email">Email address:</label>'
            '<ul class="errorlist" id="id_email_error">'
            "<li>This field is required.</li></ul>"
            '<input type="email" name="email" autocomplete="email" maxlength="254" '
            'required  aria-invalid="true" aria-describedby="id_email_error" '
            'id="id_email"></div>',
            html=True,
        )