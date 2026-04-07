def test_intersection(self):
        qs1 = Author.objects.annotate(
            book_alice=FilteredRelation(
                "book", condition=Q(book__title__iexact="poem by alice")
            ),
        ).filter(book_alice__isnull=False)
        qs2 = Author.objects.annotate(
            book_jane=FilteredRelation(
                "book", condition=Q(book__title__iexact="the book by jane a")
            ),
        ).filter(book_jane__isnull=False)
        self.assertSequenceEqual(qs1.intersection(qs2), [])