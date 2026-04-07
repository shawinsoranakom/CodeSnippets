def test_options_override_settings_proper_values(self):
        settings_port = 444
        options_port = 555
        self.assertNotEqual(settings_port, options_port, "test pre-req")
        expected_args = [
            "mysql",
            "--user=optionuser",
            "--host=optionhost",
            "--port=%s" % options_port,
            "optiondbname",
        ]
        expected_env = {"MYSQL_PWD": "optionpassword"}
        for keys in [("database", "password"), ("db", "passwd")]:
            with self.subTest(keys=keys):
                database, password = keys
                self.assertEqual(
                    self.settings_to_cmd_args_env(
                        {
                            "NAME": "settingdbname",
                            "USER": "settinguser",
                            "PASSWORD": "settingpassword",
                            "HOST": "settinghost",
                            "PORT": settings_port,
                            "OPTIONS": {
                                database: "optiondbname",
                                "user": "optionuser",
                                password: "optionpassword",
                                "host": "optionhost",
                                "port": options_port,
                            },
                        }
                    ),
                    (expected_args, expected_env),
                )