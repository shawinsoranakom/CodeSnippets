def test_request_accepts_none(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = ""
        self.assertIs(request.accepts("application/json"), False)
        self.assertEqual(request.accepted_types, [])
        self.assertIsNone(
            request.get_preferred_type(["application/json", "text/plain"])
        )