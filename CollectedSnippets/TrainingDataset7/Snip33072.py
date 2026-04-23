def test_slugify_lazy_string(self):
        lazy_str = lazy(lambda string: string, str)
        self.assertEqual(
            slugify(
                lazy_str(
                    " Jack & Jill like numbers 1,2,3 and 4 and silly characters ?%.$!/"
                )
            ),
            "jack-jill-like-numbers-123-and-4-and-silly-characters",
        )