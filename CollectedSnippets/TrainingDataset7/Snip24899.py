def test_nl_redirect(self):
        response = self.client.get(
            "/profiel/registreren/", headers={"accept-language": "nl"}
        )
        self.assertRedirects(response, "/nl/profiel/registreren/")

        response = self.client.get(response.headers["location"])
        self.assertEqual(response.status_code, 200)