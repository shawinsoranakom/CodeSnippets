def test_csrf_protect_decorator(self):
        @csrf_protect
        def sync_view(request):
            return HttpResponse()

        request = self.get_request()
        response = sync_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIs(request.csrf_processing_done, True)

        with self.assertLogs("django.security.csrf", "WARNING"):
            request = self.get_request(token=None)
            response = sync_view(request)
            self.assertEqual(response.status_code, 403)