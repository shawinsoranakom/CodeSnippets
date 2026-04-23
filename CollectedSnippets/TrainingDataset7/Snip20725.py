def test_never_cache_decorator_headers(self, mocked_time):
        @never_cache
        def a_view(request):
            return HttpResponse()

        mocked_time.return_value = 1167616461.0
        response = a_view(HttpRequest())
        self.assertEqual(
            response.headers["Expires"],
            "Mon, 01 Jan 2007 01:54:21 GMT",
        )
        self.assertEqual(
            response.headers["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )