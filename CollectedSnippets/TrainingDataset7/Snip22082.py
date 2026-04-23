def test_with_m2m(self):
        qs = Author.objects.annotate(
            favorite_books_written_by_jane=FilteredRelation(
                "favorite_books",
                condition=Q(favorite_books__in=[self.book2]),
            ),
        ).filter(favorite_books_written_by_jane__isnull=False)
        self.assertSequenceEqual(qs, [self.author1])