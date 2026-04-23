def test_wrapped_async_function_is_coroutine_function(self):
        async def async_view(request):
            return HttpResponse()

        wrapped_view = csrf_exempt(async_view)
        self.assertIs(iscoroutinefunction(wrapped_view), True)