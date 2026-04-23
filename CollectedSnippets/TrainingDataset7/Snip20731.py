def test_never_cache_decorator_http_request_proxy(self):
        class MyClass:
            @method_decorator(never_cache)
            def a_view(self, request):
                return HttpResponse()

        request = HttpRequest()
        response = MyClass().a_view(HttpRequestProxy(request))
        self.assertIn("Cache-Control", response.headers)
        self.assertIn("Expires", response.headers)