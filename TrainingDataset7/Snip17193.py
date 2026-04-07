def test_combined_annotation_commutative(self):
        book1 = Book.objects.annotate(adjusted_rating=F("rating") + 2).get(
            pk=self.b1.pk
        )
        book2 = Book.objects.annotate(adjusted_rating=2 + F("rating")).get(
            pk=self.b1.pk
        )
        self.assertEqual(book1.adjusted_rating, book2.adjusted_rating)
        book1 = Book.objects.annotate(adjusted_rating=F("rating") + None).get(
            pk=self.b1.pk
        )
        book2 = Book.objects.annotate(adjusted_rating=None + F("rating")).get(
            pk=self.b1.pk
        )
        self.assertIs(book1.adjusted_rating, None)
        self.assertEqual(book1.adjusted_rating, book2.adjusted_rating)