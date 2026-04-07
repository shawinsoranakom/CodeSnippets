def test_unprefixed_language_other_than_accept_language(self):
        response = self.client.get("/simple/", HTTP_ACCEPT_LANGUAGE="fr")
        self.assertEqual(response.content, b"Yes")