def test_learn_cache_key(self):
        request = self.factory.head(self.path)
        response = HttpResponse()
        response.headers["Vary"] = "Pony"
        # Make sure that the Vary header is added to the key hash
        learn_cache_key(request, response)

        self.assertEqual(
            get_cache_key(request),
            "views.decorators.cache.cache_page.settingsprefix.GET."
            "18a03f9c9649f7d684af5db3524f5c99.d41d8cd98f00b204e9800998ecf8427e",
        )