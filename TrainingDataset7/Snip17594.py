def test_passwordchangeform_clean_old_password_sensitive_variables(self):
        password_form = PasswordChangeForm(User())
        password_form.cleaned_data = {"old_password": self.sensitive_password}
        password_form.error_messages = None
        try:
            password_form.clean_old_password()
        except TypeError:
            exc_info = sys.exc_info()

        rf = RequestFactory()
        response = technical_500_response(rf.get("/"), *exc_info)
        self.assertNotContains(response, self.sensitive_password, status_code=500)

        self.assertContains(
            response,
            '<tr><td>old_password</td><td class="code">'
            "<pre>&#x27;********************&#x27;</pre></td></tr>",
            html=True,
            status_code=500,
        )