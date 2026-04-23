def test_cache_write_unpicklable_object(self):
        fetch_middleware = FetchFromCacheMiddleware(empty_response)

        request = self.factory.get("/cache/test")
        request._cache_update_cache = True
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertIsNone(get_cache_data)

        content = "Testing cookie serialization."

        def get_response(req):
            response = HttpResponse(content)
            response.set_cookie("foo", "bar")
            return response

        update_middleware = UpdateCacheMiddleware(get_response)
        response = update_middleware(request)

        get_cache_data = fetch_middleware.process_request(request)
        self.assertIsNotNone(get_cache_data)
        self.assertEqual(get_cache_data.content, content.encode())
        self.assertEqual(get_cache_data.cookies, response.cookies)

        UpdateCacheMiddleware(lambda req: get_cache_data)(request)
        get_cache_data = fetch_middleware.process_request(request)
        self.assertIsNotNone(get_cache_data)
        self.assertEqual(get_cache_data.content, content.encode())
        self.assertEqual(get_cache_data.cookies, response.cookies)