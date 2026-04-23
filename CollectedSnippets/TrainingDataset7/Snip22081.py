def test_exclude_relation_with_join(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_alice=FilteredRelation(
                    "book", condition=~Q(book__title__icontains="alice")
                ),
            )
            .filter(book_alice__isnull=False)
            .distinct(),
            [self.author2],
        )