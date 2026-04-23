def test_valid_secret_not_replaced_on_GET(self):
        """
        Masked and unmasked CSRF cookies are not replaced during a GET request.
        """
        cases = [
            TEST_SECRET,
            MASKED_TEST_SECRET1,
        ]
        for cookie in cases:
            with self.subTest(cookie=cookie):
                req = self._get_request(cookie=cookie)
                resp = protected_view(req)
                self.assertContains(resp, "OK")
                csrf_cookie = self._read_csrf_cookie(req, resp)
                self.assertFalse(csrf_cookie, msg="A CSRF cookie was sent.")