def test_vary_on_cookie_decorator(self):
        @vary_on_cookie
        def sync_view(request):
            return HttpResponse()

        response = sync_view(HttpRequest())
        self.assertEqual(response.get("Vary"), "Cookie")