def test_escaping(self):
        # Force a language via GET otherwise the gettext functions are a noop!
        response = self.client.get("/jsi18n_admin/?language=de")
        self.assertContains(response, "\\x04")