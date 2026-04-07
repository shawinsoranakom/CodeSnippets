def test_values_annotation(self):
        """
        Annotations can reference fields in a values clause,
        and contribute to an existing values clause.
        """
        # annotate references a field in values()
        qs = Book.objects.values("rating").annotate(other_rating=F("rating") - 1)
        book = qs.get(pk=self.b1.pk)
        self.assertEqual(book["rating"] - 1, book["other_rating"])

        # filter refs the annotated value
        book = qs.get(other_rating=4)
        self.assertEqual(book["other_rating"], 4)

        # can annotate an existing values with a new field
        book = qs.annotate(other_isbn=F("isbn")).get(other_rating=4)
        self.assertEqual(book["other_rating"], 4)
        self.assertEqual(book["other_isbn"], "155860191")