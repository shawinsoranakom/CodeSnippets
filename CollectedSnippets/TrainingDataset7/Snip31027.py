def test_no_matching_accepted_type(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "text/html"

        self.assertIsNone(
            request.get_preferred_type(["application/json", "text/plain"])
        )