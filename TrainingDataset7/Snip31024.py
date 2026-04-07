def test_request_accepts_some(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = (
            "text/html,application/xhtml+xml,application/xml;q=0.9"
        )
        self.assertIs(request.accepts("text/html"), True)
        self.assertIs(request.accepts("application/xhtml+xml"), True)
        self.assertIs(request.accepts("application/xml"), True)
        self.assertIs(request.accepts("application/json"), False)