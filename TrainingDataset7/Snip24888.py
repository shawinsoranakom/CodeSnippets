def test_request_urlconf_considered(self):
        request = RequestFactory().get("/nl/")
        request.urlconf = "i18n.patterns.urls.default"
        middleware = LocaleMiddleware(lambda req: HttpResponse())
        with translation.override("nl"):
            middleware.process_request(request)
        self.assertEqual(request.LANGUAGE_CODE, "nl")