def test_log_message(self):
        request = WSGIRequest(self.request_factory.get("/").environ)
        request.makefile = lambda *args, **kwargs: BytesIO()
        handler = WSGIRequestHandler(request, "192.168.0.2", None)
        level_status_codes = {
            "info": [200, 301, 304],
            "warning": [400, 403, 404],
            "error": [500, 503],
        }
        for level, status_codes in level_status_codes.items():
            for status_code in status_codes:
                # The correct level gets the message.
                with self.assertLogs("django.server", level.upper()) as cm:
                    handler.log_message("GET %s %s", "A", str(status_code))
                self.assertIn("GET A %d" % status_code, cm.output[0])
                # Incorrect levels don't have any messages.
                for wrong_level in level_status_codes:
                    if wrong_level != level:
                        with self.assertLogs("django.server", "INFO") as cm:
                            handler.log_message("GET %s %s", "A", str(status_code))
                        self.assertNotEqual(
                            cm.records[0].levelname, wrong_level.upper()
                        )