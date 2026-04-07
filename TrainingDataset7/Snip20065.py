def test_invalid_cookie_replaced_on_GET(self):
        """
        A CSRF cookie with the wrong format is replaced during a GET request.
        """
        req = self._get_request(cookie="badvalue")
        resp = protected_view(req)
        self.assertContains(resp, "OK")
        csrf_cookie = self._read_csrf_cookie(req, resp)
        self.assertTrue(csrf_cookie, msg="No CSRF cookie was sent.")
        self.assertEqual(len(csrf_cookie), CSRF_SECRET_LENGTH)