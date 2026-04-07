def test_wrapped_sync_function_is_not_coroutine_function(self):
        def sync_view(request):
            return HttpResponse()

        wrapped_view = login_required(sync_view)
        self.assertIs(iscoroutinefunction(wrapped_view), False)