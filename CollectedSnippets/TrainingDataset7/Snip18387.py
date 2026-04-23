def test_default_logout_then_login_get(self):
        self.login()
        req = HttpRequest()
        req.method = "GET"
        req.META["SERVER_NAME"] = "testserver"
        req.META["SERVER_PORT"] = 80
        req.session = self.client.session
        response = logout_then_login(req)
        self.assertEqual(response.status_code, 405)