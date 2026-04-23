async def test_cache_control_empty_decorator_async_view(self):
        @cache_control()
        async def async_view(request):
            return HttpResponse()

        response = await async_view(HttpRequest())
        self.assertEqual(response.get("Cache-Control"), "")