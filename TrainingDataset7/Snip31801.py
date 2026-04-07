def test_broken_pipe_errors(self):
        """WSGIServer handles broken pipe errors."""
        request = WSGIRequest(self.request_factory.get("/").environ)
        client_address = ("192.168.2.0", 8080)
        msg = f"- Broken pipe from {client_address}"
        tests = [
            BrokenPipeError,
            ConnectionAbortedError,
            ConnectionResetError,
        ]
        for exception in tests:
            with self.subTest(exception=exception):
                try:
                    server = WSGIServer(("localhost", 0), WSGIRequestHandler)
                    try:
                        raise exception()
                    except Exception:
                        with captured_stderr() as err:
                            with self.assertLogs("django.server", "INFO") as cm:
                                server.handle_error(request, client_address)
                        self.assertEqual(err.getvalue(), "")
                        self.assertEqual(cm.records[0].getMessage(), msg)
                finally:
                    server.server_close()