async def test_exempt_decorator_async_view(self):
        @xframe_options_exempt
        async def an_async_view(request):
            return HttpResponse()

        request = HttpRequest()
        response = await an_async_view(request)
        self.assertIsNone(response.get("X-Frame-Options"))
        self.assertIs(response.xframe_options_exempt, True)

        # The real purpose of the exempt decorator is to suppress the
        # middleware's functionality.
        middleware_response = await XFrameOptionsMiddleware(an_async_view)(request)
        self.assertIsNone(middleware_response.get("X-Frame-Options"))