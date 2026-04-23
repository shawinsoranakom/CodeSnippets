async def test_require_safe_accepts_only_safe_methods_async_view(self):
        @require_safe
        async def async_view(request):
            return HttpResponse("OK")

        request = HttpRequest()
        request.method = "GET"
        self.assertIsInstance(await async_view(request), HttpResponse)
        request.method = "HEAD"
        self.assertIsInstance(await async_view(request), HttpResponse)
        request.method = "POST"
        self.assertIsInstance(await async_view(request), HttpResponseNotAllowed)
        request.method = "PUT"
        self.assertIsInstance(await async_view(request), HttpResponseNotAllowed)
        request.method = "DELETE"
        self.assertIsInstance(await async_view(request), HttpResponseNotAllowed)