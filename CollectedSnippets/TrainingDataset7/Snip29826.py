def test_invalid_pages_per_range(self):
        with self.assertRaisesMessage(
            ValueError, "pages_per_range must be None or a positive integer"
        ):
            BrinIndex(fields=["title"], name="test_title_brin", pages_per_range=0)