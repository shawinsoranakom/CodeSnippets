def test_wrapped_async_function_is_coroutine_function(self):
        async def async_view(request):
            return HttpResponse()

        wrapped_view = require_http_methods(["GET"])(async_view)
        self.assertIs(iscoroutinefunction(wrapped_view), True)