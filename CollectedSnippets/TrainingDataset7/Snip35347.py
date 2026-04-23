def test_setup_test_environment_calling_more_than_once(self):
        with self.assertRaisesMessage(
            RuntimeError, "setup_test_environment() was already called"
        ):
            setup_test_environment()