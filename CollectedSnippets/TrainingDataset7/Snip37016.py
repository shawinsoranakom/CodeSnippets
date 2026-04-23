def test_setlang_cookie(self):
        # we force saving language to a cookie rather than a session
        # by excluding session middleware and those which do require it
        test_settings = {
            "MIDDLEWARE": ["django.middleware.common.CommonMiddleware"],
            "LANGUAGE_COOKIE_NAME": "mylanguage",
            "LANGUAGE_COOKIE_AGE": 3600 * 7 * 2,
            "LANGUAGE_COOKIE_DOMAIN": ".example.com",
            "LANGUAGE_COOKIE_PATH": "/test/",
            "LANGUAGE_COOKIE_HTTPONLY": True,
            "LANGUAGE_COOKIE_SAMESITE": "Strict",
            "LANGUAGE_COOKIE_SECURE": True,
        }
        with self.settings(**test_settings):
            post_data = {"language": "pl", "next": "/views/"}
            response = self.client.post("/i18n/setlang/", data=post_data)
            language_cookie = response.cookies.get("mylanguage")
            self.assertEqual(language_cookie.value, "pl")
            self.assertEqual(language_cookie["domain"], ".example.com")
            self.assertEqual(language_cookie["path"], "/test/")
            self.assertEqual(language_cookie["max-age"], 3600 * 7 * 2)
            self.assertIs(language_cookie["httponly"], True)
            self.assertEqual(language_cookie["samesite"], "Strict")
            self.assertIs(language_cookie["secure"], True)