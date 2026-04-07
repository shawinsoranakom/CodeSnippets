def test_nl_path(self):
        response = self.client.get("/nl/profiel/registreren-als-pad/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-language"], "nl")
        self.assertEqual(response.context["LANGUAGE_CODE"], "nl")