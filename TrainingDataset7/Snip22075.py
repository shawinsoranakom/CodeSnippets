def test_with_join_and_complex_condition(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book",
                    condition=Q(
                        Q(book__title__iexact="poem by alice")
                        | Q(book__state=Book.RENTED)
                    ),
                ),
            ).filter(book_alice__isnull=False),
            [self.author1],
        )