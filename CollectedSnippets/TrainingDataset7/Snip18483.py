def test_runshell_use_environ(self):
        for env in [None, {}]:
            with self.subTest(env=env):
                with mock.patch("subprocess.run") as run:
                    with mock.patch.object(
                        BaseDatabaseClient,
                        "settings_to_cmd_args_env",
                        return_value=([], env),
                    ):
                        self.client.runshell(None)
                    run.assert_called_once_with([], env=None, check=True)