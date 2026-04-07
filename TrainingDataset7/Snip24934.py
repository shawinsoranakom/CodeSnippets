def test_multiple_locales(self):
        with override_settings(LOCALE_PATHS=[os.path.join(self.test_dir, "locale")]):
            call_command("compilemessages", locale=["hr", "fr"], verbosity=0)

            self.assertTrue(os.path.exists(self.MO_FILE_HR))
            self.assertTrue(os.path.exists(self.MO_FILE_FR))