def test_parameters(self):
        self.assertEqual(
            self.settings_to_cmd_args_env({"NAME": "test.db.sqlite3"}, ["-help"]),
            (["sqlite3", "test.db.sqlite3", "-help"], None),
        )