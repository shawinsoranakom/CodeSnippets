def test_accept_header_priority_overlapping_mime(self):
        request = HttpRequest()
        request.META["HTTP_ACCEPT"] = "text/*;q=0.8,text/html;q=0.8"

        self.assertEqual(
            [str(accepted_type) for accepted_type in request.accepted_types],
            [
                "text/html; q=0.8",
                "text/*; q=0.8",
            ],
        )
        self.assertEqual(
            [
                str(accepted_type)
                for accepted_type in request.accepted_types_by_precedence
            ],
            [
                "text/html; q=0.8",
                "text/*; q=0.8",
            ],
        )