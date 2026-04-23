def test_setpasswordform_validate_passwords_sensitive_variables(self):
        password_form = SetPasswordForm(AnonymousUser())
        password_form.cleaned_data = {
            "password1": self.sensitive_password,
            "password2": self.sensitive_password + "2",
        }
        try:
            password_form.validate_passwords()
        except ValueError:
            exc_info = sys.exc_info()

        rf = RequestFactory()
        response = technical_500_response(rf.get("/"), *exc_info)
        self.assertNotContains(response, self.sensitive_password, status_code=500)
        self.assertNotContains(response, self.sensitive_password + "2", status_code=500)

        self.assertContains(
            response,
            '<tr><td>password1</td><td class="code">'
            "<pre>&#x27;********************&#x27;</pre></td></tr>",
            html=True,
            status_code=500,
        )

        self.assertContains(
            response,
            '<tr><td>password2</td><td class="code">'
            "<pre>&#x27;********************&#x27;</pre></td></tr>",
            html=True,
            status_code=500,
        )