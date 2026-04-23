def test_cache_control_full_decorator(self):
        @cache_control(max_age=123, private=True, public=True, custom=456)
        def a_view(request):
            return HttpResponse()

        response = a_view(HttpRequest())
        cache_control_items = response.get("Cache-Control").split(", ")
        self.assertEqual(
            set(cache_control_items), {"max-age=123", "private", "public", "custom=456"}
        )