def test_nofuzzy_compiling(self):
        with override_settings(LOCALE_PATHS=[os.path.join(self.test_dir, "locale")]):
            call_command("compilemessages", locale=[self.LOCALE], verbosity=0)
            with translation.override(self.LOCALE):
                self.assertEqual(gettext("Lenin"), "Ленин")
                self.assertEqual(gettext("Vodka"), "Vodka")