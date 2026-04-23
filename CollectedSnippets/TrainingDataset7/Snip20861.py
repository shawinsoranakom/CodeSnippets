async def test_conditional_page_decorator_successful_async_view(self):
        @conditional_page
        async def async_view(request):
            response = HttpResponse()
            response.content = b"test"
            response["Cache-Control"] = "public"
            return response

        request = HttpRequest()
        request.method = "GET"
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.get("Etag"))