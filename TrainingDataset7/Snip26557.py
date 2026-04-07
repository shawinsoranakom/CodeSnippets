def test_content_type_on(self):
        """
        With SECURE_CONTENT_TYPE_NOSNIFF set to True, the middleware adds
        "X-Content-Type-Options: nosniff" header to the response.
        """
        self.assertEqual(
            self.process_response().headers["X-Content-Type-Options"],
            "nosniff",
        )