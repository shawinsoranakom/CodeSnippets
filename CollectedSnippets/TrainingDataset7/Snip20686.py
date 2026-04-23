def test_parameters(self):
        self.assertEqual(
            self.settings_to_cmd_args_env(
                {
                    "NAME": "somedbname",
                    "USER": None,
                    "PASSWORD": None,
                    "HOST": None,
                    "PORT": None,
                    "OPTIONS": {},
                },
                ["--help"],
            ),
            (["mysql", "somedbname", "--help"], None),
        )