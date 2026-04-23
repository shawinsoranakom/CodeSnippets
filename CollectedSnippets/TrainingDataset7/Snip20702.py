def test_parameters(self):
        self.assertEqual(
            self.settings_to_cmd_args_env({"NAME": "dbname"}, ["--help"]),
            (["psql", "--help", "dbname"], None),
        )