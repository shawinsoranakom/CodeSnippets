def test_non_english_default_english_userpref(self):
        """
        Same as above with the difference that there IS an 'en' translation
        available. The JavaScript i18n view must return a NON empty language
        catalog with the proper English translations. See #13726 for more
        details.
        """
        with self.settings(LANGUAGE_CODE="fr"), override("en-us"):
            response = self.client.get("/jsi18n_english_translation/")
            self.assertContains(response, "this app0 string is to be translated")