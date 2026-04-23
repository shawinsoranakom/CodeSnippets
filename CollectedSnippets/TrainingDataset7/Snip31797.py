def test_https(self):
        request = WSGIRequest(self.request_factory.get("/").environ)
        request.makefile = lambda *args, **kwargs: BytesIO()

        handler = WSGIRequestHandler(request, "192.168.0.2", None)

        with self.assertLogs("django.server", "ERROR") as cm:
            handler.log_message("GET %s %s", "\x16\x03", "4")
        self.assertEqual(
            "You're accessing the development server over HTTPS, "
            "but it only supports HTTP.",
            cm.records[0].getMessage(),
        )