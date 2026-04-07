def test_csrf_token_on_404_stays_constant(self):
        response = self.client.get("/does not exist/")
        # The error handler returns status code 599.
        self.assertEqual(response.status_code, 599)
        response.charset = "ascii"
        token1 = response.text
        response = self.client.get("/does not exist/")
        self.assertEqual(response.status_code, 599)
        response.charset = "ascii"
        token2 = response.text
        secret2 = _unmask_cipher_token(token2)
        self.assertMaskedSecretCorrect(token1, secret2)