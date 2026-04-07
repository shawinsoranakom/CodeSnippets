def test_templateresponse_from_process_view_passed_to_process_template_response(
        self,
    ):
        """
        TemplateResponses returned from process_view() should be passed to any
        template response middleware.
        """
        response = self.client.get("/middleware_exceptions/view/")
        expected_lines = [
            b"Processed view normal_view",
            b"ProcessViewTemplateResponseMiddleware",
            b"TemplateResponseMiddleware",
        ]
        self.assertEqual(response.content, b"\n".join(expected_lines))