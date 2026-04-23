def test_rotate_token(self):
        request = HttpRequest()
        request.META["CSRF_COOKIE"] = TEST_SECRET
        self.assertNotIn("CSRF_COOKIE_NEEDS_UPDATE", request.META)
        rotate_token(request)
        # The underlying secret was changed.
        cookie = request.META["CSRF_COOKIE"]
        self.assertEqual(len(cookie), CSRF_SECRET_LENGTH)
        self.assertNotEqual(cookie, TEST_SECRET)
        self.assertIs(request.META["CSRF_COOKIE_NEEDS_UPDATE"], True)