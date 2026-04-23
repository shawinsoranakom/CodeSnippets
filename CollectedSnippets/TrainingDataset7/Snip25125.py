def test_locale_paths_override_app_translation(self):
        with self.settings(INSTALLED_APPS=["i18n.resolution"]):
            self.assertGettext("Time", "LOCALE_PATHS")