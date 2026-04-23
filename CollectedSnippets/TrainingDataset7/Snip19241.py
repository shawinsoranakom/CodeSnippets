def test_cache_key_no_i18n(self):
        request = self.factory.get(self.path)
        lang = translation.get_language()
        tz = timezone.get_current_timezone_name()
        response = HttpResponse()
        key = learn_cache_key(request, response)
        self.assertNotIn(
            lang,
            key,
            "Cache keys shouldn't include the language name when i18n isn't active",
        )
        self.assertNotIn(
            tz,
            key,
            "Cache keys shouldn't include the time zone name when i18n isn't active",
        )