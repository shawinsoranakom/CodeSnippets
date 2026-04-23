def test_default_logout_then_login(self):
        self.login()
        req = HttpRequest()
        req.method = "POST"
        csrf_token = get_token(req)
        req.COOKIES[settings.CSRF_COOKIE_NAME] = csrf_token
        req.POST = {"csrfmiddlewaretoken": csrf_token}
        req.META["SERVER_NAME"] = "testserver"
        req.META["SERVER_PORT"] = 80
        req.session = self.client.session
        response = logout_then_login(req)
        self.confirm_logged_out()
        self.assertRedirects(response, "/login/", fetch_redirect_response=False)