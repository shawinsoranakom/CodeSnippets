def test_wrapped_async_function_is_coroutine_function(self):
        async def async_view(request):
            return HttpResponse()

        wrapped_view = cache_control()(async_view)
        self.assertIs(iscoroutinefunction(wrapped_view), True)