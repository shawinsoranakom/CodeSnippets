def test_no_headers(self):
        """Absence of Accept header defaults to '*/*'."""
        request = HttpRequest()
        self.assertEqual(
            [str(accepted_type) for accepted_type in request.accepted_types],
            ["*/*"],
        )