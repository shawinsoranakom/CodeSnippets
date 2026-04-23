async def test_never_cache_decorator_expires_not_overridden_async_view(self):
        @never_cache
        async def async_view(request):
            return HttpResponse(headers={"Expires": "tomorrow"})

        response = await async_view(HttpRequest())
        self.assertEqual(response.headers["Expires"], "tomorrow")