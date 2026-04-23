def test_templateresponse_from_process_view_rendered(self):
        """
        TemplateResponses returned from process_view() must be rendered before
        being passed to any middleware that tries to access response.content,
        such as middleware_exceptions.middleware.LogMiddleware.
        """
        response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(
            response.content,
            b"Processed view normal_view\nProcessViewTemplateResponseMiddleware",
        )