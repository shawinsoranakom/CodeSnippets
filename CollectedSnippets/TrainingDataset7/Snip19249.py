def test_view_decorator(self):
        # decorate the same view with different cache decorators
        default_view = cache_page(3)(hello_world_view)
        default_with_prefix_view = cache_page(3, key_prefix="prefix1")(hello_world_view)

        explicit_default_view = cache_page(3, cache="default")(hello_world_view)
        explicit_default_with_prefix_view = cache_page(
            3, cache="default", key_prefix="prefix1"
        )(hello_world_view)

        other_view = cache_page(1, cache="other")(hello_world_view)
        other_with_prefix_view = cache_page(1, cache="other", key_prefix="prefix2")(
            hello_world_view
        )

        request = self.factory.get("/view/")

        # Request the view once
        response = default_view(request, "1")
        self.assertEqual(response.content, b"Hello World 1")

        # Request again -- hit the cache
        response = default_view(request, "2")
        self.assertEqual(response.content, b"Hello World 1")

        # Requesting the same view with the explicit cache should yield the
        # same result
        response = explicit_default_view(request, "3")
        self.assertEqual(response.content, b"Hello World 1")

        # Requesting with a prefix will hit a different cache key
        response = explicit_default_with_prefix_view(request, "4")
        self.assertEqual(response.content, b"Hello World 4")

        # Hitting the same view again gives a cache hit
        response = explicit_default_with_prefix_view(request, "5")
        self.assertEqual(response.content, b"Hello World 4")

        # And going back to the implicit cache will hit the same cache
        response = default_with_prefix_view(request, "6")
        self.assertEqual(response.content, b"Hello World 4")

        # Requesting from an alternate cache won't hit cache
        response = other_view(request, "7")
        self.assertEqual(response.content, b"Hello World 7")

        # But a repeated hit will hit cache
        response = other_view(request, "8")
        self.assertEqual(response.content, b"Hello World 7")

        # And prefixing the alternate cache yields yet another cache entry
        response = other_with_prefix_view(request, "9")
        self.assertEqual(response.content, b"Hello World 9")

        # But if we wait a couple of seconds...
        time.sleep(2)

        # ... the default cache will still hit
        caches["default"]
        response = default_view(request, "11")
        self.assertEqual(response.content, b"Hello World 1")

        # ... the default cache with a prefix will still hit
        response = default_with_prefix_view(request, "12")
        self.assertEqual(response.content, b"Hello World 4")

        # ... the explicit default cache will still hit
        response = explicit_default_view(request, "13")
        self.assertEqual(response.content, b"Hello World 1")

        # ... the explicit default cache with a prefix will still hit
        response = explicit_default_with_prefix_view(request, "14")
        self.assertEqual(response.content, b"Hello World 4")

        # .. but a rapidly expiring cache won't hit
        response = other_view(request, "15")
        self.assertEqual(response.content, b"Hello World 15")

        # .. even if it has a prefix
        response = other_with_prefix_view(request, "16")
        self.assertEqual(response.content, b"Hello World 16")