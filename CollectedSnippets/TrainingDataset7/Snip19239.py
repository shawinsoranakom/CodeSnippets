def test_cache_key_i18n_translation_accept_language(self):
        lang = translation.get_language()
        self.assertEqual(lang, "en")
        request = self.factory.get(self.path)
        request.META["HTTP_ACCEPT_ENCODING"] = "gzip;q=1.0, identity; q=0.5, *;q=0"
        response = HttpResponse()
        response.headers["Vary"] = "accept-encoding"
        key = learn_cache_key(request, response)
        self.assertIn(
            lang,
            key,
            "Cache keys should include the language name when translation is active",
        )
        self.check_accept_language_vary(
            "en-us", "cookie, accept-language, accept-encoding", key
        )
        self.check_accept_language_vary(
            "en-US", "cookie, accept-encoding, accept-language", key
        )
        self.check_accept_language_vary(
            "en-US,en;q=0.8", "accept-encoding, accept-language, cookie", key
        )
        self.check_accept_language_vary(
            "en-US,en;q=0.8,ko;q=0.6", "accept-language, cookie, accept-encoding", key
        )
        self.check_accept_language_vary(
            "ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3 ",
            "accept-encoding, cookie, accept-language",
            key,
        )
        self.check_accept_language_vary(
            "ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4",
            "accept-language, accept-encoding, cookie",
            key,
        )
        self.check_accept_language_vary(
            "ko;q=1.0,en;q=0.5", "cookie, accept-language, accept-encoding", key
        )
        self.check_accept_language_vary(
            "ko, en", "cookie, accept-encoding, accept-language", key
        )
        self.check_accept_language_vary(
            "ko-KR, en-US", "accept-encoding, accept-language, cookie", key
        )