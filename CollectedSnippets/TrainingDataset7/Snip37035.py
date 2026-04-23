def test_i18n_different_non_english_languages(self):
        """
        Similar to above but with neither default or requested language being
        English.
        """
        with self.settings(LANGUAGE_CODE="fr"), override("es-ar"):
            response = self.client.get("/jsi18n_multi_packages2/")
            self.assertContains(response, "este texto de app3 debe ser traducido")