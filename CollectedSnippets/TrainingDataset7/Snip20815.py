def test_csrf_exempt_decorator(self):
        @csrf_exempt
        def sync_view(request):
            return HttpResponse()

        self.assertIs(sync_view.csrf_exempt, True)
        self.assertIsInstance(sync_view(HttpRequest()), HttpResponse)