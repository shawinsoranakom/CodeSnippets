def test_app_locale_compiled(self):
        call_command("compilemessages", locale=[self.LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PROJECT_MO_FILE))
        self.assertTrue(os.path.exists(self.APP_MO_FILE))