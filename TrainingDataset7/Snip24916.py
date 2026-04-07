def test_en_path(self):
        response = self.client.get("/en/account/register-as-path/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-language"], "en")
        self.assertEqual(response.context["LANGUAGE_CODE"], "en")