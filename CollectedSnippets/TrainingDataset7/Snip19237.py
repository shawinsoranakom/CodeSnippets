def test_cache_key_i18n_translation(self):
        request = self.factory.get(self.path)
        lang = translation.get_language()
        response = HttpResponse()
        key = learn_cache_key(request, response)
        self.assertIn(
            lang,
            key,
            "Cache keys should include the language name when translation is active",
        )
        key2 = get_cache_key(request)
        self.assertEqual(key, key2)