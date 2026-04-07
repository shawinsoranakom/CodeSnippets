async def test_no_append_slash_decorator_async_view(self):
        @no_append_slash
        async def async_view(request):
            return HttpResponse()

        self.assertIs(async_view.should_append_slash, False)
        self.assertIsInstance(await async_view(HttpRequest()), HttpResponse)