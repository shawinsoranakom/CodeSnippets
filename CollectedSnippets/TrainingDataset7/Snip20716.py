async def test_cache_control_decorator_http_request_async_view(self):
        class MyClass:
            @cache_control(a="b")
            async def async_view(self, request):
                return HttpResponse()

        msg = (
            "cache_control didn't receive an HttpRequest. If you are decorating a "
            "classmethod, be sure to use @method_decorator."
        )
        request = HttpRequest()
        with self.assertRaisesMessage(TypeError, msg):
            await MyClass().async_view(request)
        with self.assertRaisesMessage(TypeError, msg):
            await MyClass().async_view(HttpRequestProxy(request))