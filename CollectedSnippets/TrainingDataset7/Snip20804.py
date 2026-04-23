async def test_csrf_protect_decorator_async_view(self):
        @csrf_protect
        async def async_view(request):
            return HttpResponse()

        request = self.get_request()
        response = await async_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIs(request.csrf_processing_done, True)

        with self.assertLogs("django.security.csrf", "WARNING"):
            request = self.get_request(token=None)
            response = await async_view(request)
            self.assertEqual(response.status_code, 403)