def test_jsi18n_fallback_language(self):
        """
        Let's make sure that the fallback language is still working properly
        in cases where the selected language cannot be found.
        """
        with self.settings(LANGUAGE_CODE="fr"), override("fi"):
            response = self.client.get("/jsi18n/")
            self.assertContains(response, "il faut le traduire")
            self.assertNotContains(response, "Untranslated string")