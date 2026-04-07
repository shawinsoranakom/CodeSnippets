def test_cache_page_timeout(self):
        # Page timeout takes precedence over the "max-age" section of the
        # "Cache-Control".
        tests = [
            (1, 3),  # max_age < page_timeout.
            (3, 1),  # max_age > page_timeout.
        ]
        for max_age, page_timeout in tests:
            with self.subTest(max_age=max_age, page_timeout=page_timeout):
                view = cache_page(timeout=page_timeout)(
                    cache_control(max_age=max_age)(hello_world_view)
                )
                request = self.factory.get("/view/")
                response = view(request, "1")
                self.assertEqual(response.content, b"Hello World 1")
                time.sleep(1)
                response = view(request, "2")
                self.assertEqual(
                    response.content,
                    b"Hello World 1" if page_timeout > max_age else b"Hello World 2",
                )
            cache.clear()