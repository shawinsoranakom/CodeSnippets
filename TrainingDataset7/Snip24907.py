def test_en_redirect(self):
        response = self.client.get(
            "/account/register", headers={"accept-language": "en"}, follow=True
        )
        # We only want one redirect, bypassing CommonMiddleware
        self.assertEqual(response.redirect_chain, [("/en/account/register/", 302)])
        self.assertRedirects(response, "/en/account/register/", 302)

        response = self.client.get(
            "/prefixed.xml", headers={"accept-language": "en"}, follow=True
        )
        self.assertRedirects(response, "/en/prefixed.xml", 302)