def test_setting_timeout_from_environment_variable(self):
        self.assertEqual(self.RELOADER_CLS().client_timeout, 10)