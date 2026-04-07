def test_get_cache_key(self):
        request = self.factory.get(self.path)
        template = engines["django"].from_string("This is a test")
        response = TemplateResponse(HttpRequest(), template)
        key_prefix = "localprefix"
        # Expect None if no headers have been set yet.
        self.assertIsNone(get_cache_key(request))
        # Set headers to an empty list.
        learn_cache_key(request, response)

        self.assertEqual(
            get_cache_key(request),
            "views.decorators.cache.cache_page.settingsprefix.GET."
            "58a0a05c8a5620f813686ff969c26853.d41d8cd98f00b204e9800998ecf8427e",
        )
        # A specified key_prefix is taken into account.
        learn_cache_key(request, response, key_prefix=key_prefix)
        self.assertEqual(
            get_cache_key(request, key_prefix=key_prefix),
            "views.decorators.cache.cache_page.localprefix.GET."
            "58a0a05c8a5620f813686ff969c26853.d41d8cd98f00b204e9800998ecf8427e",
        )