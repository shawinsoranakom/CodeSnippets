def test_lang_from_translated_i18n_pattern(self):
        response = self.client.post(
            "/i18n/setlang/",
            data={"language": "nl"},
            follow=True,
            headers={"referer": "/en/translated/"},
        )
        self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, "nl")
        self.assertRedirects(response, "/nl/vertaald/")
        # And reverse
        response = self.client.post(
            "/i18n/setlang/",
            data={"language": "en"},
            follow=True,
            headers={"referer": "/nl/vertaald/"},
        )
        self.assertRedirects(response, "/en/translated/")