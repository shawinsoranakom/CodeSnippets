def test_translated_path_prefixed_language_other_than_cookie_language(self):
        self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: "nl"})
        response = self.client.get("/en/users/")
        self.assertEqual(response.status_code, 200)