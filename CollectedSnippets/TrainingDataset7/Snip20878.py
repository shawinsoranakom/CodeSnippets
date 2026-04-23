def test_vary_on_headers_decorator(self):
        @vary_on_headers("Header", "Another-header")
        def sync_view(request):
            return HttpResponse()

        response = sync_view(HttpRequest())
        self.assertEqual(response.get("Vary"), "Header, Another-header")