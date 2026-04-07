def test_i18n_patterns_returns_list(self):
        with override_settings(USE_I18N=False):
            self.assertIsInstance(i18n_patterns([]), list)
        with override_settings(USE_I18N=True):
            self.assertIsInstance(i18n_patterns([]), list)