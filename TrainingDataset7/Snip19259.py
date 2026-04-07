def test_get_cache_key_with_query(self):
        request = self.factory.get(self.path, {"test": 1})
        template = engines["django"].from_string("This is a test")
        response = TemplateResponse(HttpRequest(), template)
        # Expect None if no headers have been set yet.
        self.assertIsNone(get_cache_key(request))
        # Set headers to an empty list.
        learn_cache_key(request, response)
        # The querystring is taken into account.
        self.assertEqual(
            get_cache_key(request),
            "views.decorators.cache.cache_page.settingsprefix.GET."
            "0f1c2d56633c943073c4569d9a9502fe.d41d8cd98f00b204e9800998ecf8427e",
        )