def test_content_type_off(self):
        """
        With SECURE_CONTENT_TYPE_NOSNIFF False, the middleware does not add an
        "X-Content-Type-Options" header to the response.
        """
        self.assertNotIn("X-Content-Type-Options", self.process_response().headers)