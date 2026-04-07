def test_304_response_has_http_caching_headers_but_not_cached(self):
        original_view = mock.Mock(return_value=HttpResponseNotModified())
        view = cache_page(2)(original_view)
        request = self.factory.get("/view/")
        # The view shouldn't be cached on the second call.
        view(request).close()
        response = view(request)
        response.close()
        self.assertEqual(original_view.call_count, 2)
        self.assertIsInstance(response, HttpResponseNotModified)
        self.assertIn("Cache-Control", response)
        self.assertIn("Expires", response)