def test_already_configured(self):
        with self.assertRaisesMessage(RuntimeError, "Settings already configured."):
            settings.configure()