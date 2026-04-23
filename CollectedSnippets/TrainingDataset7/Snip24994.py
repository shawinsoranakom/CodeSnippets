def test_no_duplicate_locale_paths(self):
        for locale_paths in [
            [],
            [os.path.join(self.test_dir, "locale")],
            [Path(self.test_dir, "locale")],
        ]:
            with self.subTest(locale_paths=locale_paths):
                with override_settings(LOCALE_PATHS=locale_paths):
                    cmd = MakeMessagesCommand()
                    management.call_command(cmd, locale=["en", "ru"], verbosity=0)
                    self.assertTrue(
                        all(isinstance(path, str) for path in cmd.locale_paths)
                    )
                    self.assertEqual(len(cmd.locale_paths), len(set(cmd.locale_paths)))