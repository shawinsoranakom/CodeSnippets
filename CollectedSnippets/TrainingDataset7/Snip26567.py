def test_referrer_policy_already_present(self):
        """
        The middleware will not override a "Referrer-Policy" header already
        present in the response.
        """
        response = self.process_response(headers={"Referrer-Policy": "unsafe-url"})
        self.assertEqual(response.headers["Referrer-Policy"], "unsafe-url")