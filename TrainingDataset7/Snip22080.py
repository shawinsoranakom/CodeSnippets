def test_multiple_times(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_title_alice=FilteredRelation(
                    "book", condition=Q(book__title__icontains="alice")
                ),
            )
            .filter(book_title_alice__isnull=False)
            .filter(book_title_alice__isnull=False)
            .distinct(),
            [self.author1],
        )