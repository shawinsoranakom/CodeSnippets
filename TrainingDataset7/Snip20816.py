async def test_csrf_exempt_decorator_async_view(self):
        @csrf_exempt
        async def async_view(request):
            return HttpResponse()

        self.assertIs(async_view.csrf_exempt, True)
        self.assertIsInstance(await async_view(HttpRequest()), HttpResponse)