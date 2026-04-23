def test_values_fields_annotations_order(self):
        qs = Book.objects.annotate(other_rating=F("rating") - 1).values(
            "other_rating", "rating"
        )
        book = qs.get(pk=self.b1.pk)
        self.assertEqual(
            list(book.items()),
            [("other_rating", self.b1.rating - 1), ("rating", self.b1.rating)],
        )