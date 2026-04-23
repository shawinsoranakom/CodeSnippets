async def test_gzip_page_decorator_async_view(self):
        @gzip_page
        async def async_view(request):
            return HttpResponse(content=self.content)

        request = HttpRequest()
        request.META["HTTP_ACCEPT_ENCODING"] = "gzip"
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Encoding"), "gzip")