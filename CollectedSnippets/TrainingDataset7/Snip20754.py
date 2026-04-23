async def test_decorator_sets_x_frame_options_to_deny_async_view(self):
        @xframe_options_deny
        async def an_async_view(request):
            return HttpResponse()

        response = await an_async_view(HttpRequest())
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")