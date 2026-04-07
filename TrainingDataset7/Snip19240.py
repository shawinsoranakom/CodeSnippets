def test_cache_key_i18n_timezone(self):
        request = self.factory.get(self.path)
        tz = timezone.get_current_timezone_name()
        response = HttpResponse()
        key = learn_cache_key(request, response)
        self.assertIn(
            tz,
            key,
            "Cache keys should include the time zone name when time zones are active",
        )
        key2 = get_cache_key(request)
        self.assertEqual(key, key2)