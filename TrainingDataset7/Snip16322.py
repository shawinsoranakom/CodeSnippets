def test_i18n_language_non_english_default(self):
        """
        Check if the JavaScript i18n view returns an empty language catalog
        if the default language is non-English but the selected language
        is English. See #13388 and #3594 for more details.
        """
        with self.settings(LANGUAGE_CODE="fr"), translation.override("en-us"):
            response = self.client.get(reverse("admin:jsi18n"))
            self.assertNotContains(response, "Choisir une heure")