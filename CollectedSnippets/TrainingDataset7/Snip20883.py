async def test_vary_on_cookie_decorator_async_view(self):
        @vary_on_cookie
        async def async_view(request):
            return HttpResponse()

        response = await async_view(HttpRequest())
        self.assertEqual(response.get("Vary"), "Cookie")