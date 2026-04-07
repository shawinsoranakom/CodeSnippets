def test_cache_control_empty_decorator(self):
        @cache_control()
        def a_view(request):
            return HttpResponse()

        response = a_view(HttpRequest())
        self.assertEqual(response.get("Cache-Control"), "")