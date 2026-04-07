def test_precedence(self):
        """
        Taken from https://datatracker.ietf.org/doc/html/rfc7231#section-5.3.2.
        """
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = (
            "text/*, text/plain, text/plain;format=flowed, */*"
        )
        self.assertEqual(
            [
                str(accepted_type)
                for accepted_type in request.accepted_types_by_precedence
            ],
            [
                "text/plain; format=flowed",
                "text/plain",
                "text/*",
                "*/*",
            ],
        )