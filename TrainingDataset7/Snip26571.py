def test_coop_already_present(self):
        """
        The middleware doesn't override a "Cross-Origin-Opener-Policy" header
        already present in the response.
        """
        response = self.process_response(
            headers={"Cross-Origin-Opener-Policy": "same-origin"}
        )
        self.assertEqual(response.headers["Cross-Origin-Opener-Policy"], "same-origin")