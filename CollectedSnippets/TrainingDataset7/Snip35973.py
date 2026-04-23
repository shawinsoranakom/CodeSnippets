def test_subparser_non_django_error_formatting(self):
        self.write_settings("settings.py", apps=["user_commands"])
        out, err = self.run_manage(["subparser_vanilla", "foo", "seven"])
        self.assertNoOutput(out)
        err_lines = err.splitlines()
        self.assertEqual(len(err_lines), 2)
        self.assertEqual(
            err_lines[1],
            "manage.py subparser_vanilla foo: error: argument bar: invalid int value: "
            "'seven'",
        )