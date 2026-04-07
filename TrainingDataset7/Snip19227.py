def test_get_cache_key(self):
        request = self.factory.get(self.path)
        response = HttpResponse()
        # Expect None if no headers have been set yet.
        self.assertIsNone(get_cache_key(request))
        # Set headers to an empty list.
        learn_cache_key(request, response)

        self.assertEqual(
            get_cache_key(request),
            "views.decorators.cache.cache_page.settingsprefix.GET."
            "18a03f9c9649f7d684af5db3524f5c99.d41d8cd98f00b204e9800998ecf8427e",
        )
        # A specified key_prefix is taken into account.
        key_prefix = "localprefix"
        learn_cache_key(request, response, key_prefix=key_prefix)
        self.assertEqual(
            get_cache_key(request, key_prefix=key_prefix),
            "views.decorators.cache.cache_page.localprefix.GET."
            "18a03f9c9649f7d684af5db3524f5c99.d41d8cd98f00b204e9800998ecf8427e",
        )