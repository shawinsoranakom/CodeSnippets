def test_custom_bad_request_template(self):
        response = self.client.get("/raises400/")
        self.assertIs(response.wsgi_request, response.context.request)