def test_fuzzy_compiling(self):
        with override_settings(LOCALE_PATHS=[os.path.join(self.test_dir, "locale")]):
            call_command(
                "compilemessages", locale=[self.LOCALE], fuzzy=True, verbosity=0
            )
            with translation.override(self.LOCALE):
                self.assertEqual(gettext("Lenin"), "Ленин")
                self.assertEqual(gettext("Vodka"), "Водка")