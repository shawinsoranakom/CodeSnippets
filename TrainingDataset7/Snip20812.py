async def test_ensure_csrf_cookie_decorator_async_view(self):
        @ensure_csrf_cookie
        async def async_view(request):
            return HttpResponse()

        request = self.get_request()
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIs(request.csrf_processing_done, True)

        with self.assertNoLogs("django.security.csrf", "WARNING"):
            request = self.get_request(token=None)
            response = await async_view(request)
            self.assertEqual(response.status_code, 200)