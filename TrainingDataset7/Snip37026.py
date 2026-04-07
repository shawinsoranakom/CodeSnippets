def test_jsi18n_fallback_language_with_custom_locale_dir(self):
        """
        The fallback language works when there are several levels of fallback
        translation catalogs.
        """
        locale_paths = [
            path.join(
                path.dirname(path.dirname(path.abspath(__file__))),
                "custom_locale_path",
            ),
        ]
        with self.settings(LOCALE_PATHS=locale_paths), override("es_MX"):
            response = self.client.get("/jsi18n/")
            self.assertContains(
                response, "custom_locale_path: esto tiene que ser traducido"
            )
            response = self.client.get("/jsi18n_no_packages/")
            self.assertContains(
                response, "custom_locale_path: esto tiene que ser traducido"
            )