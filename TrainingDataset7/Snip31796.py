def test_log_message_escapes_control_sequences(self):
        request = WSGIRequest(self.request_factory.get("/").environ)
        request.makefile = lambda *args, **kwargs: BytesIO()
        handler = WSGIRequestHandler(request, "192.168.0.2", None)

        malicious_path = "\x1b[31mALERT\x1b[0m"

        with self.assertLogs("django.server", "WARNING") as cm:
            handler.log_message("GET %s %s", malicious_path, "404")

        log = cm.output[0]

        self.assertNotIn("\x1b[31m", log)
        self.assertIn("\\x1b[31mALERT\\x1b[0m", log)