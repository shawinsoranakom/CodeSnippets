def test_nl_url(self):
        response = self.client.get("/nl/profiel/registreren/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-language"], "nl")
        self.assertEqual(response.context["LANGUAGE_CODE"], "nl")