def test_not_allowed_repr_no_content_type(self):
        response = HttpResponseNotAllowed(("GET", "POST"))
        del response.headers["Content-Type"]
        self.assertEqual(
            repr(response), "<HttpResponseNotAllowed [GET, POST] status_code=405>"
        )