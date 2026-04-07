def test_wrapped_sync_function_is_not_coroutine_function(self):
        def sync_view(request):
            return HttpResponse()

        wrapped_view = csrf_exempt(sync_view)
        self.assertIs(iscoroutinefunction(wrapped_view), False)