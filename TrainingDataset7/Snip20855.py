def test_wrapped_async_function_is_coroutine_function(self):
        async def async_view(request):
            return HttpResponse()

        wrapped_view = condition(
            etag_func=self.etag_func, last_modified_func=self.latest_entry
        )(async_view)
        self.assertIs(iscoroutinefunction(wrapped_view), True)