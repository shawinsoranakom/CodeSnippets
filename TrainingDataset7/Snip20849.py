async def test_require_http_methods_methods_async_view(self):
        @require_http_methods(["GET", "PUT"])
        async def my_view(request):
            return HttpResponse("OK")

        request = HttpRequest()
        request.method = "GET"
        self.assertIsInstance(await my_view(request), HttpResponse)
        request.method = "PUT"
        self.assertIsInstance(await my_view(request), HttpResponse)
        request.method = "HEAD"
        self.assertIsInstance(await my_view(request), HttpResponseNotAllowed)
        request.method = "POST"
        self.assertIsInstance(await my_view(request), HttpResponseNotAllowed)
        request.method = "DELETE"
        self.assertIsInstance(await my_view(request), HttpResponseNotAllowed)