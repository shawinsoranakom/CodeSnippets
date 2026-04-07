def test_column(self):
        self.assertEqual(
            self.settings_to_cmd_args_env(
                {
                    "NAME": "dbname",
                    "USER": "some:user",
                    "PASSWORD": "some:password",
                    "HOST": "::1",
                    "PORT": "444",
                }
            ),
            (
                ["psql", "-U", "some:user", "-h", "::1", "-p", "444", "dbname"],
                {"PGPASSWORD": "some:password"},
            ),
        )