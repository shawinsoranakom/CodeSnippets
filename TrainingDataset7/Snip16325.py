def test_jsi18n_format_fallback(self):
        """
        The JavaScript i18n view doesn't return localized date/time formats
        when the selected language cannot be found.
        """
        with self.settings(LANGUAGE_CODE="ru"), translation.override("none"):
            response = self.client.get(reverse("admin:jsi18n"))
            self.assertNotContains(response, "%d.%m.%Y %H:%M:%S")
            self.assertContains(response, "%Y-%m-%d %H:%M:%S")