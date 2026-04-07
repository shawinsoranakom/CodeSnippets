def teardown_test_environment(self, **kwargs):
        unittest.removeHandler()
        teardown_test_environment()