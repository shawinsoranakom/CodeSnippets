def test_delete_cookie_secure_prefix(self):
        """
        delete_cookie() sets the secure flag if the cookie name starts with
        __Host- or __Secure- (without that, browsers ignore cookies with those
        prefixes).
        """
        response = HttpResponse()
        for prefix in ("Secure", "Host"):
            with self.subTest(prefix=prefix):
                cookie_name = "__%s-c" % prefix
                response.delete_cookie(cookie_name)
                self.assertIs(response.cookies[cookie_name]["secure"], True)