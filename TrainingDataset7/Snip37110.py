def test_wsgi_cookies(self):
        response_data = {}

        def start_response(status, headers):
            response_data["headers"] = headers

        application = get_wsgi_application()
        environ = self.request_factory._base_environ(
            PATH_INFO="/cookie/", REQUEST_METHOD="GET"
        )
        application(environ, start_response)
        self.assertIn(("Set-Cookie", "key=value; Path=/"), response_data["headers"])