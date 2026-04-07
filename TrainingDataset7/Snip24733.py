def test_handle_accepts_httpstatus_enum_value(self):
        def start_response(status, headers):
            start_response.status = status

        environ = self.request_factory.get("/httpstatus_enum/").environ
        WSGIHandler()(environ, start_response)
        self.assertEqual(start_response.status, "200 OK")