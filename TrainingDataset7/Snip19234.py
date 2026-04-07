def test_head_caches_correctly(self):
        test_content = "test content"

        request = self.factory.head(self.path)
        request._cache_update_cache = True
        self._set_cache(request, test_content)

        request = self.factory.head(self.path)
        request._cache_update_cache = True
        get_cache_data = FetchFromCacheMiddleware(empty_response).process_request(
            request
        )
        self.assertIsNotNone(get_cache_data)
        self.assertEqual(test_content.encode(), get_cache_data.content)