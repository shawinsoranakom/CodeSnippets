def test_view_exception_converted_before_middleware(self):
        response = self.client.get("/middleware_exceptions/permission_denied/")
        self.assertEqual(mw.log, [(response.status_code, response.content)])
        self.assertEqual(response.status_code, 403)