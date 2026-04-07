def test_sts_already_present(self):
        """
        The middleware will not override a "Strict-Transport-Security" header
        already present in the response.
        """
        response = self.process_response(
            secure=True, headers={"Strict-Transport-Security": "max-age=7200"}
        )
        self.assertEqual(response.headers["Strict-Transport-Security"], "max-age=7200")