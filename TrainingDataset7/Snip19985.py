def test_get_token_csrf_cookie_not_set(self):
        request = HttpRequest()
        self.assertNotIn("CSRF_COOKIE", request.META)
        self.assertNotIn("CSRF_COOKIE_NEEDS_UPDATE", request.META)
        token = get_token(request)
        cookie = request.META["CSRF_COOKIE"]
        self.assertMaskedSecretCorrect(token, cookie)
        self.assertIs(request.META["CSRF_COOKIE_NEEDS_UPDATE"], True)