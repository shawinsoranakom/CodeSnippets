def test_confirm_custom_reset_url_token_link_redirects_to_set_password_page(self):
        url, path = self._test_confirm_start()
        path = path.replace("/reset/", "/reset/custom/token/")
        client = Client()
        response = client.get(path)
        token = response.resolver_match.kwargs["token"]
        uuidb64 = response.resolver_match.kwargs["uidb64"]
        self.assertRedirects(
            response, "/reset/custom/token/%s/set-passwordcustom/" % uuidb64
        )
        self.assertEqual(client.session["_password_reset_token"], token)