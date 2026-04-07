def test_select_for_update(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_jane=FilteredRelation(
                    "book", condition=Q(book__title__iexact="the book by jane a")
                ),
            )
            .filter(book_jane__isnull=False)
            .select_for_update(),
            [self.author2],
        )