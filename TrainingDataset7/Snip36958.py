def test_settings_with_sensitive_keys(self):
        """
        The debug page should filter out some sensitive information found in
        dict settings.
        """
        for setting in self.sensitive_settings:
            FOOBAR = {
                setting: "should not be displayed",
                "recursive": {setting: "should not be displayed"},
            }
            with self.subTest(setting=setting):
                with self.settings(DEBUG=True, FOOBAR=FOOBAR):
                    response = self.client.get("/raises500/")
                    self.assertNotContains(
                        response, "should not be displayed", status_code=500
                    )