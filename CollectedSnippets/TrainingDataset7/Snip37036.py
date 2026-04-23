def test_i18n_with_locale_paths(self):
        extended_locale_paths = settings.LOCALE_PATHS + [
            path.join(
                path.dirname(path.dirname(path.abspath(__file__))),
                "app3",
                "locale",
            ),
        ]
        with self.settings(LANGUAGE_CODE="es-ar", LOCALE_PATHS=extended_locale_paths):
            with override("es-ar"):
                response = self.client.get("/jsi18n/")
                self.assertContains(response, "este texto de app3 debe ser traducido")