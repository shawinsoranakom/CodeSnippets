def test_extra(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=Q(book__title__iexact="poem by alice")
                ),
            )
            .filter(book_alice__isnull=False)
            .extra(where=["1 = 1"]),
            [self.author1],
        )