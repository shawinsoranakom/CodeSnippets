def test_parse_language_cookie(self):
        g = get_language_from_request
        request = self.rf.get("/")
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = "pt-br"
        self.assertEqual("pt-br", g(request))

        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = "pt"
        self.assertEqual("pt", g(request))

        request = self.rf.get("/", headers={"accept-language": "de"})
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = "es"
        self.assertEqual("es", g(request))

        # There isn't a Django translation to a US variation of the Spanish
        # language, a safe assumption. When the user sets it as the preferred
        # language, the main 'es' translation should be selected instead.
        request = self.rf.get("/")
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = "es-us"
        self.assertEqual(g(request), "es")
        # There isn't a main language (zh) translation of Django but there is a
        # translation to variation (zh-hans) the user sets zh-hans as the
        # preferred language, it should be selected without falling back nor
        # ignoring it.
        request = self.rf.get("/", headers={"accept-language": "de"})
        request.COOKIES[settings.LANGUAGE_COOKIE_NAME] = "zh-hans"
        self.assertEqual(g(request), "zh-hans")