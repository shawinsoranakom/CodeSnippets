def test_no_session_on_request(self):
        msg = (
            "CSRF_USE_SESSIONS is enabled, but request.session is not set. "
            "SessionMiddleware must appear before CsrfViewMiddleware in MIDDLEWARE."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            mw = CsrfViewMiddleware(lambda req: HttpResponse())
            mw.process_request(HttpRequest())