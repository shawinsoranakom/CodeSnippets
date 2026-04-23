def test_middleware(self):
        def set_cache(request, lang, msg):
            def get_response(req):
                return HttpResponse(msg)

            translation.activate(lang)
            return UpdateCacheMiddleware(get_response)(request)

        # cache with non empty request.GET
        request = self.factory.get(self.path, {"foo": "bar", "other": "true"})
        request._cache_update_cache = True

        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        # first access, cache must return None
        self.assertIsNone(get_cache_data)
        content = "Check for cache with QUERY_STRING"

        def get_response(req):
            return HttpResponse(content)

        UpdateCacheMiddleware(get_response)(request)
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        # cache must return content
        self.assertIsNotNone(get_cache_data)
        self.assertEqual(get_cache_data.content, content.encode())
        # different QUERY_STRING, cache must be empty
        request = self.factory.get(self.path, {"foo": "bar", "somethingelse": "true"})
        request._cache_update_cache = True
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertIsNone(get_cache_data)

        # i18n tests
        en_message = "Hello world!"
        es_message = "Hola mundo!"

        request = self.factory.get(self.path)
        request._cache_update_cache = True
        set_cache(request, "en", en_message)
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        # The cache can be recovered
        self.assertIsNotNone(get_cache_data)
        self.assertEqual(get_cache_data.content, en_message.encode())
        # change the session language and set content
        request = self.factory.get(self.path)
        request._cache_update_cache = True
        set_cache(request, "es", es_message)
        # change again the language
        translation.activate("en")
        # retrieve the content from cache
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertEqual(get_cache_data.content, en_message.encode())
        # change again the language
        translation.activate("es")
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertEqual(get_cache_data.content, es_message.encode())
        # reset the language
        translation.deactivate()