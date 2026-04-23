def test_path_name(self):
        self.assertEqual(
            self.settings_to_cmd_args_env({"NAME": Path("test.db.sqlite3")}),
            (["sqlite3", Path("test.db.sqlite3")], None),
        )