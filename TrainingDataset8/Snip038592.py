def test_maybe_read_env_variable(self):
        self.assertEqual(
            "env:RANDOM_TEST", config._maybe_read_env_variable("env:RANDOM_TEST")
        )
        os.environ["RANDOM_TEST"] = "1234"
        self.assertEqual(1234, config._maybe_read_env_variable("env:RANDOM_TEST"))