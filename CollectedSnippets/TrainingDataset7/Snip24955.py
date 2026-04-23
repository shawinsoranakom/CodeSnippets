def test_locale_paths_pathlib(self):
        with override_settings(LOCALE_PATHS=[Path(self.test_dir) / "canned_locale"]):
            call_command("compilemessages", locale=["fr"], verbosity=0)
            self.assertTrue(os.path.exists("canned_locale/fr/LC_MESSAGES/django.mo"))