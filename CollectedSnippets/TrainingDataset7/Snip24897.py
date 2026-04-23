def test_en_redirect(self):
        response = self.client.get(
            "/account/register/", headers={"accept-language": "en"}
        )
        self.assertRedirects(response, "/en/account/register/")

        response = self.client.get(response.headers["location"])
        self.assertEqual(response.status_code, 200)