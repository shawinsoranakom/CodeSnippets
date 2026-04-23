def test_translated_path_prefixed_language_other_than_accepted_header(self):
        response = self.client.get("/en/users/", headers={"accept-language": "nl"})
        self.assertEqual(response.status_code, 200)