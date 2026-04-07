def test_never_cache_decorator_http_request(self):
        class MyClass:
            @never_cache
            def a_view(self, request):
                return HttpResponse()

        request = HttpRequest()
        msg = (
            "never_cache didn't receive an HttpRequest. If you are decorating "
            "a classmethod, be sure to use @method_decorator."
        )
        with self.assertRaisesMessage(TypeError, msg):
            MyClass().a_view(request)
        with self.assertRaisesMessage(TypeError, msg):
            MyClass().a_view(HttpRequestProxy(request))