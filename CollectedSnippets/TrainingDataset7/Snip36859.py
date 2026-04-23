def test_no_cookies(self):
        """
        The CSRF cookie is checked for POST. Failure to send this cookie should
        provide a nice error message.
        """
        response = self.client.post("/")
        self.assertContains(
            response,
            "You are seeing this message because this site requires a CSRF "
            "cookie when submitting forms. This cookie is required for "
            "security reasons, to ensure that your browser is not being "
            "hijacked by third parties.",
            status_code=403,
        )