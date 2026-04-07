def test_content_type_already_present(self):
        """
        The middleware will not override an "X-Content-Type-Options" header
        already present in the response.
        """
        response = self.process_response(
            secure=True, headers={"X-Content-Type-Options": "foo"}
        )
        self.assertEqual(response.headers["X-Content-Type-Options"], "foo")