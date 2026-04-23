def test_process_template_response(self):
        response = self.client.get("/middleware_exceptions/template_response/")
        self.assertEqual(
            response.content, b"template_response OK\nTemplateResponseMiddleware"
        )