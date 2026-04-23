def test_translated_path_unprefixed_language_other_than_cookie_language(self):
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "en"})
        response = self.client.get("/gebruikers/")
        self.assertEqual(response.status_code, 200)