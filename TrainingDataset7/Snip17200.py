def test_defer_annotation(self):
        """
        Deferred attributes can be referenced by an annotation,
        but they are not themselves deferred, and cannot be deferred.
        """
        qs = Book.objects.defer("rating").annotate(other_rating=F("rating") - 1)

        with self.assertNumQueries(2):
            book = qs.get(other_rating=4)
            self.assertEqual(book.rating, 5)
            self.assertEqual(book.other_rating, 4)

        with self.assertRaisesMessage(
            FieldDoesNotExist, "Book has no field named 'other_rating'"
        ):
            book = qs.defer("other_rating").get(other_rating=4)