def test_middleware(self):
        middleware = CacheMiddleware(hello_world_view)
        prefix_middleware = CacheMiddleware(hello_world_view, key_prefix="prefix1")
        timeout_middleware = CacheMiddleware(hello_world_view, cache_timeout=1)

        request = self.factory.get("/view/")

        # Put the request through the request middleware
        result = middleware.process_request(request)
        self.assertIsNone(result)

        response = hello_world_view(request, "1")

        # Now put the response through the response middleware
        response = middleware.process_response(request, response)

        # Repeating the request should result in a cache hit
        result = middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.content, b"Hello World 1")

        # The same request through a different middleware won't hit
        result = prefix_middleware.process_request(request)
        self.assertIsNone(result)

        # The same request with a timeout _will_ hit
        result = timeout_middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.content, b"Hello World 1")