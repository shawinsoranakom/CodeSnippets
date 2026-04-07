def test_non_BMP_char(self):
        """
        Non-BMP characters should not break the javascript_catalog (#21725).
        """
        with self.settings(LANGUAGE_CODE="en-us"), override("fr"):
            response = self.client.get("/jsi18n/app5/")
            self.assertContains(response, "emoji")
            self.assertContains(response, "\\ud83d\\udca9")