def test_full_dec_normal(self):
        """
        All methods of middleware are called for normal HttpResponses
        """

        @full_dec
        def normal_view(request):
            template = engines["django"].from_string("Hello world")
            return HttpResponse(template.render())

        request = self.rf.get("/")
        normal_view(request)
        self.assertTrue(getattr(request, "process_request_reached", False))
        self.assertTrue(getattr(request, "process_view_reached", False))
        # process_template_response must not be called for HttpResponse
        self.assertFalse(getattr(request, "process_template_response_reached", False))
        self.assertTrue(getattr(request, "process_response_reached", False))