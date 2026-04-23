def test_logout_preserve_language(self):
        """Language is preserved after logout."""
        self.login()
        self.client.post("/setlang/", {"language": "pl"})
        self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, "pl")
        self.client.post("/logout/")
        self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE_NAME].value, "pl")