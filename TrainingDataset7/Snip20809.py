def test_wrapped_sync_function_is_not_coroutine_function(self):
        def sync_view(request):
            return HttpResponse()

        wrapped_view = ensure_csrf_cookie(sync_view)
        self.assertIs(iscoroutinefunction(wrapped_view), False)