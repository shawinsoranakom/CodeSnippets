def test_slugify(self):
        self.assertEqual(
            slugify(
                " Jack & Jill like numbers 1,2,3 and 4 and silly characters ?%.$!/"
            ),
            "jack-jill-like-numbers-123-and-4-and-silly-characters",
        )