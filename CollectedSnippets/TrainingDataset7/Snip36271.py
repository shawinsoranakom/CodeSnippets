def test_full_dec_templateresponse(self):
        """
        All methods of middleware are called for TemplateResponses in
        the right sequence.
        """

        @full_dec
        def template_response_view(request):
            template = engines["django"].from_string("Hello world")
            return TemplateResponse(request, template)

        request = self.rf.get("/")
        response = template_response_view(request)
        self.assertTrue(getattr(request, "process_request_reached", False))
        self.assertTrue(getattr(request, "process_view_reached", False))
        self.assertTrue(getattr(request, "process_template_response_reached", False))
        # response must not be rendered yet.
        self.assertFalse(response._is_rendered)
        # process_response must not be called until after response is rendered,
        # otherwise some decorators like csrf_protect and gzip_page will not
        # work correctly. See #16004
        self.assertFalse(getattr(request, "process_response_reached", False))
        response.render()
        self.assertTrue(getattr(request, "process_response_reached", False))
        # process_response saw the rendered content
        self.assertEqual(request.process_response_content, b"Hello world")