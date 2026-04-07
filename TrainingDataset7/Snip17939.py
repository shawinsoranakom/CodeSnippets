def test_i18n(self):
        # 'Julia' with accented 'u':
        management.get_system_username = lambda: "J\xfalia"
        self.assertEqual(management.get_default_username(), "julia")