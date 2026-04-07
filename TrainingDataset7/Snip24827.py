def test_not_allowed_repr(self):
        response = HttpResponseNotAllowed(["GET", "OPTIONS"], content_type="text/plain")
        expected = (
            '<HttpResponseNotAllowed [GET, OPTIONS] status_code=405, "text/plain">'
        )
        self.assertEqual(repr(response), expected)