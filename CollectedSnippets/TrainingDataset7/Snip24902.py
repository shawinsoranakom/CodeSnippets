def test_pl_pl_redirect(self):
        # language from outside of the supported LANGUAGES list
        response = self.client.get(
            "/account/register/", headers={"accept-language": "pl-pl"}
        )
        self.assertRedirects(response, "/en/account/register/")

        response = self.client.get(response.headers["location"])
        self.assertEqual(response.status_code, 200)