def test_i18n_language_non_english_default(self):
        """
        Check if the JavaScript i18n view returns an empty language catalog
        if the default language is non-English, the selected language
        is English and there is not 'en' translation available. See #13388,
        #3594 and #13726 for more details.
        """
        with self.settings(LANGUAGE_CODE="fr"), override("en-us"):
            response = self.client.get("/jsi18n/")
            self.assertNotContains(response, "Choisir une heure")