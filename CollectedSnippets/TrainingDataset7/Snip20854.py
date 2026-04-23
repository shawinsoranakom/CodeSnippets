def test_wrapped_sync_function_is_not_coroutine_function(self):
        def sync_view(request):
            return HttpResponse()

        wrapped_view = condition(
            etag_func=self.etag_func, last_modified_func=self.latest_entry
        )(sync_view)
        self.assertIs(iscoroutinefunction(wrapped_view), False)