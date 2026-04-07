def test_without_join(self):
        self.assertCountEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=Q(book__title__iexact="poem by alice")
                ),
            ),
            [self.author1, self.author2],
        )