def test_basic(self):
        self.assertEqual(
            self.settings_to_cmd_args_env(
                {
                    "NAME": "dbname",
                    "USER": "someuser",
                    "PASSWORD": "somepassword",
                    "HOST": "somehost",
                    "PORT": "444",
                }
            ),
            (
                ["psql", "-U", "someuser", "-h", "somehost", "-p", "444", "dbname"],
                {"PGPASSWORD": "somepassword"},
            ),
        )