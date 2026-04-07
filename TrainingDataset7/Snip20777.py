def test_no_append_slash_decorator(self):
        @no_append_slash
        def sync_view(request):
            return HttpResponse()

        self.assertIs(sync_view.should_append_slash, False)
        self.assertIsInstance(sync_view(HttpRequest()), HttpResponse)