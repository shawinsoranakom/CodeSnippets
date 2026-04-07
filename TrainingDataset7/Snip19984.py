def test_get_token_csrf_cookie_set(self):
        request = HttpRequest()
        request.META["CSRF_COOKIE"] = TEST_SECRET
        self.assertNotIn("CSRF_COOKIE_NEEDS_UPDATE", request.META)
        token = get_token(request)
        self.assertMaskedSecretCorrect(token, TEST_SECRET)
        # The existing cookie is preserved.
        self.assertEqual(request.META["CSRF_COOKIE"], TEST_SECRET)
        self.assertIs(request.META["CSRF_COOKIE_NEEDS_UPDATE"], True)