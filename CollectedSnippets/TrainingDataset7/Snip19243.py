def test_middleware_doesnt_cache_streaming_response(self):
        request = self.factory.get(self.path)
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertIsNone(get_cache_data)

        def get_stream_response(req):
            return StreamingHttpResponse(["Check for cache with streaming content."])

        UpdateCacheMiddleware(get_stream_response)(request)

        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertIsNone(get_cache_data)