def test_cache_resetting(self):
        """
        After setting LANGUAGE, the cache should be cleared and languages
        previously valid should not be used (#14170).
        """
        g = get_language_from_request
        request = self.rf.get("/", headers={"accept-language": "pt-br"})
        self.assertEqual("pt-br", g(request))
        with self.settings(LANGUAGES=[("en", "English")]):
            self.assertNotEqual("pt-br", g(request))