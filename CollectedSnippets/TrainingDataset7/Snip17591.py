def test_login_process_sensitive_variables(self):
        try:
            self.client.post(
                reverse("login"),
                dict(username="testusername", password=self.sensitive_password),
            )
        except TypeError:
            exc_info = sys.exc_info()

        rf = RequestFactory()
        with patch("django.views.debug.ExceptionReporter", FilteredExceptionReporter):
            response = technical_500_response(rf.get("/"), *exc_info)

        self.assertNotContains(response, self.sensitive_password, status_code=500)
        self.assertContains(response, "TypeErrorBackend", status_code=500)

        # AuthenticationForm.clean().
        self.assertContains(
            response,
            '<tr><td>password</td><td class="code">'
            "<pre>&#39;********************&#39;</pre></td></tr>",
            html=True,
            status_code=500,
        )