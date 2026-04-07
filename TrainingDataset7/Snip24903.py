def test_custom_redirect_class(self):
        response = self.client.get(
            "/account/register/", headers={"accept-language": "en"}
        )
        self.assertRedirects(response, "/en/account/register/", 301)