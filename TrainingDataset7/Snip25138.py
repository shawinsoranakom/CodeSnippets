def test_other_lang_with_prefix(self):
        response = self.client.get("/fr/simple/")
        self.assertEqual(response.content, b"Oui")