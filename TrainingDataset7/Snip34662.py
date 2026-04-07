def test_trace_request_from_factory(self):
        """The request factory returns an echo response for a TRACE request."""
        url_path = "/somewhere/"
        request = self.request_factory.trace(url_path)
        response = trace_view(request)
        protocol = request.META["SERVER_PROTOCOL"]
        echoed_request_line = "TRACE {} {}".format(url_path, protocol)
        self.assertContains(response, echoed_request_line)