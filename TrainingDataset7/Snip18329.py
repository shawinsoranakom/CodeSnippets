def test_confirm_link_redirects_to_set_password_page(self):
        url, path = self._test_confirm_start()
        # Don't use PasswordResetConfirmClient (self.client) here which
        # automatically fetches the redirect page.
        client = Client()
        response = client.get(path)
        token = response.resolver_match.kwargs["token"]
        uuidb64 = response.resolver_match.kwargs["uidb64"]
        self.assertRedirects(response, "/reset/%s/set-password/" % uuidb64)
        self.assertEqual(client.session["_password_reset_token"], token)