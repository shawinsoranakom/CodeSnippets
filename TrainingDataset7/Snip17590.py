def test_clean_credentials_sensitive_variables(self):
        try:
            # Passing in a list to cause an exception
            _clean_credentials([1, self.sensitive_password])
        except TypeError:
            exc_info = sys.exc_info()
        rf = RequestFactory()
        response = technical_500_response(rf.get("/"), *exc_info)
        self.assertNotContains(response, self.sensitive_password, status_code=500)
        self.assertContains(
            response,
            '<tr><td>credentials</td><td class="code">'
            "<pre>&#39;********************&#39;</pre></td></tr>",
            html=True,
            status_code=500,
        )