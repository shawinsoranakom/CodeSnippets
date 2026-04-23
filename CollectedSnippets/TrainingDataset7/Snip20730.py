async def test_never_cache_decorator_http_request_async_view(self):
        class MyClass:
            @never_cache
            async def async_view(self, request):
                return HttpResponse()

        request = HttpRequest()
        msg = (
            "never_cache didn't receive an HttpRequest. If you are decorating "
            "a classmethod, be sure to use @method_decorator."
        )
        with self.assertRaisesMessage(TypeError, msg):
            await MyClass().async_view(request)
        with self.assertRaisesMessage(TypeError, msg):
            await MyClass().async_view(HttpRequestProxy(request))