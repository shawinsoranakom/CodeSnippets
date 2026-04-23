def test_ensure_csrf_cookie_decorator(self):
        @ensure_csrf_cookie
        def sync_view(request):
            return HttpResponse()

        request = self.get_request()
        response = sync_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIs(request.csrf_processing_done, True)

        with self.assertNoLogs("django.security.csrf", "WARNING"):
            request = self.get_request(token=None)
            response = sync_view(request)
            self.assertEqual(response.status_code, 200)