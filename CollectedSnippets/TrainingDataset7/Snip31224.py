def test_repr_no_content_type(self):
        response = HttpResponse(status=204)
        del response.headers["Content-Type"]
        self.assertEqual(repr(response), "<HttpResponse status_code=204>")