async def test_decorator_sets_x_frame_options_to_sameorigin_async_view(self):
        @xframe_options_sameorigin
        async def an_async_view(request):
            return HttpResponse()

        response = await an_async_view(HttpRequest())
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")