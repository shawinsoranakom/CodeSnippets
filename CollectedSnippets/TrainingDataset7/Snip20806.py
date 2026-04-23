def test_wrapped_async_function_is_coroutine_function(self):
        async def async_view(request):
            return HttpResponse()

        wrapped_view = requires_csrf_token(async_view)
        self.assertIs(iscoroutinefunction(wrapped_view), True)