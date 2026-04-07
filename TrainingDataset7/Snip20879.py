async def test_vary_on_headers_decorator_async_view(self):
        @vary_on_headers("Header", "Another-header")
        async def async_view(request):
            return HttpResponse()

        response = await async_view(HttpRequest())
        self.assertEqual(response.get("Vary"), "Header, Another-header")