def test_with_exclude(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=Q(book__title__iexact="poem by alice")
                ),
            ).exclude(book_alice__isnull=False),
            [self.author2],
        )