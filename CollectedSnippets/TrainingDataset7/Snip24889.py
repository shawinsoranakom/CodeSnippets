def test_no_lang_activate(self):
        response = self.client.get("/nl/foo/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-language"], "en")
        self.assertEqual(response.context["LANGUAGE_CODE"], "en")