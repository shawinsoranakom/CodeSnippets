def test_i18n_fallback_language_plural(self):
        """
        The fallback to a language with less plural forms maintains the real
        language's number of plural forms and correct translations.
        """
        with self.settings(LANGUAGE_CODE="pt"), override("ru"):
            response = self.client.get("/jsi18n/")
            self.assertEqual(
                response.context["catalog"]["{count} plural3"],
                ["{count} plural3 p3", "{count} plural3 p3s", "{count} plural3 p3t"],
            )
            self.assertEqual(
                response.context["catalog"]["{count} plural2"],
                ["{count} plural2", "{count} plural2s", ""],
            )
        with self.settings(LANGUAGE_CODE="ru"), override("pt"):
            response = self.client.get("/jsi18n/")
            self.assertEqual(
                response.context["catalog"]["{count} plural3"],
                ["{count} plural3", "{count} plural3s"],
            )
            self.assertEqual(
                response.context["catalog"]["{count} plural2"],
                ["{count} plural2", "{count} plural2s"],
            )