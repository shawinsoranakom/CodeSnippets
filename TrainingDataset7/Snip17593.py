def test_setpasswordform_validate_password_for_user_sensitive_variables(self):
        password_form = SetPasswordForm(AnonymousUser())
        password_form.cleaned_data = {"password2": self.sensitive_password}
        try:
            password_form.validate_password_for_user(AnonymousUser())
        except TypeError:
            exc_info = sys.exc_info()

        rf = RequestFactory()
        response = technical_500_response(rf.get("/"), *exc_info)
        self.assertNotContains(response, self.sensitive_password, status_code=500)

        self.assertContains(
            response,
            '<tr><td>password</td><td class="code">'
            "<pre>&#x27;********************&#x27;</pre></td></tr>",
            html=True,
            status_code=500,
        )