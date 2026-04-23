def test_get_wsgi_application(self):
        """
        get_wsgi_application() returns a functioning WSGI callable.
        """
        application = get_wsgi_application()

        environ = self.request_factory._base_environ(
            PATH_INFO="/", CONTENT_TYPE="text/html; charset=utf-8", REQUEST_METHOD="GET"
        )

        response_data = {}

        def start_response(status, headers):
            response_data["status"] = status
            response_data["headers"] = headers

        response = application(environ, start_response)

        self.assertEqual(response_data["status"], "200 OK")
        self.assertEqual(
            set(response_data["headers"]),
            {("Content-Length", "12"), ("Content-Type", "text/html; charset=utf-8")},
        )
        self.assertIn(
            bytes(response),
            [
                b"Content-Length: 12\r\nContent-Type: text/html; "
                b"charset=utf-8\r\n\r\nHello World!",
                b"Content-Type: text/html; "
                b"charset=utf-8\r\nContent-Length: 12\r\n\r\nHello World!",
            ],
        )