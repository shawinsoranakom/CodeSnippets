def test_pt_br_redirect(self):
        response = self.client.get(
            "/conta/registre-se/", headers={"accept-language": "pt-br"}
        )
        self.assertRedirects(response, "/pt-br/conta/registre-se/")

        response = self.client.get(response.headers["location"])
        self.assertEqual(response.status_code, 200)