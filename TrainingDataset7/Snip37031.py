def test_i18n_language_non_english_fallback(self):
        """
        Makes sure that the fallback language is still working properly
        in cases where the selected language cannot be found.
        """
        with self.settings(LANGUAGE_CODE="fr"), override("none"):
            response = self.client.get("/jsi18n/")
            self.assertContains(response, "Choisir une heure")