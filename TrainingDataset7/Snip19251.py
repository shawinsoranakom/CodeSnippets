def test_cache_control_not_cached(self):
        """
        Responses with 'Cache-Control: private/no-cache/no-store' are
        not cached.
        """
        for cc in ("private", "no-cache", "no-store"):
            with self.subTest(cache_control=cc):
                view_with_cache = cache_page(3)(
                    cache_control(**{cc: True})(hello_world_view)
                )
                request = self.factory.get("/view/")
                response = view_with_cache(request, "1")
                self.assertEqual(response.content, b"Hello World 1")
                response = view_with_cache(request, "2")
                self.assertEqual(response.content, b"Hello World 2")