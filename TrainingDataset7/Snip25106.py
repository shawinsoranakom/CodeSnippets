def test_get_custom_format(self):
        reset_format_cache()
        with self.settings(FORMAT_MODULE_PATH="i18n.other.locale"):
            with translation.override("fr", deactivate=True):
                self.assertEqual("d/m/Y CUSTOM", get_format("CUSTOM_DAY_FORMAT"))