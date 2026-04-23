def test_request_accepts_any(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "*/*"
        self.assertIs(request.accepts("application/json"), True)
        self.assertIsNone(request.get_preferred_type([]))
        self.assertEqual(
            request.get_preferred_type(["application/json", "text/plain"]),
            "application/json",
        )