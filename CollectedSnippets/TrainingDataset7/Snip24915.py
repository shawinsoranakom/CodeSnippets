def test_pt_br_url(self):
        response = self.client.get("/pt-br/conta/registre-se/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-language"], "pt-br")
        self.assertEqual(response.context["LANGUAGE_CODE"], "pt-br")