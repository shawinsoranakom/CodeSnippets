def test_en_redirect(self):
        """
        The redirect to a prefixed URL depends on 'Accept-Language' and
        'Cookie', but once prefixed no header is set.
        """
        response = self.client.get(
            "/account/register/", headers={"accept-language": "en"}
        )
        self.assertRedirects(response, "/en/account/register/")
        self.assertEqual(response.get("Vary"), "Accept-Language, Cookie")

        response = self.client.get(response.headers["location"])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get("Vary"))