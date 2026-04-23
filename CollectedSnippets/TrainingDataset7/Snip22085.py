def test_values_list(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=Q(book__title__iexact="poem by alice")
                ),
            )
            .filter(book_alice__isnull=False)
            .values_list("book_alice__title", flat=True),
            ["Poem by Alice"],
        )