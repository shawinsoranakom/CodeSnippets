def test_one_locale(self):
        with override_settings(LOCALE_PATHS=[os.path.join(self.test_dir, "locale")]):
            call_command("compilemessages", locale=["hr"], verbosity=0)

            self.assertTrue(os.path.exists(self.MO_FILE_HR))