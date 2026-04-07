def test_complex_override_warning(self):
        """Regression test for #19031"""
        msg = "Overriding setting TEST_WARN can lead to unexpected behavior."
        with self.assertWarnsMessage(UserWarning, msg) as cm:
            with override_settings(TEST_WARN="override"):
                self.assertEqual(settings.TEST_WARN, "override")
        self.assertEqual(cm.filename, __file__)