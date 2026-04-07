def test_translated_path_unprefixed_language_other_than_accepted_header(self):
        response = self.client.get("/gebruikers/", headers={"accept-language": "en"})
        self.assertEqual(response.status_code, 200)