def test_sensitive_settings(self):
        """
        The debug page should not show some sensitive settings
        (password, secret key, ...).
        """
        for setting in self.sensitive_settings:
            with self.subTest(setting=setting):
                with self.settings(DEBUG=True, **{setting: "should not be displayed"}):
                    response = self.client.get("/raises500/")
                    self.assertNotContains(
                        response, "should not be displayed", status_code=500
                    )