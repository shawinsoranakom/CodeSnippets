def test_wrapped_sync_function_is_not_coroutine_function(self):
        def sync_view(request):
            return HttpResponse()

        wrapped_view = requires_csrf_token(sync_view)
        self.assertIs(iscoroutinefunction(wrapped_view), False)