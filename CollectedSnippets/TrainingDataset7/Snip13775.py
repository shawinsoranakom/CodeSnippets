def setup_test_environment(self, **kwargs):
        setup_test_environment(debug=self.debug_mode)
        unittest.installHandler()