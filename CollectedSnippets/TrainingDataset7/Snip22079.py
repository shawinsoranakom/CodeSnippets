def test_with_multiple_filter(self):
        self.assertSequenceEqual(
            Author.objects.annotate(
                book_editor_a=FilteredRelation(
                    "book",
                    condition=Q(
                        book__title__icontains="book", book__editor_id=self.editor_a.pk
                    ),
                ),
            ).filter(book_editor_a__isnull=False),
            [self.author1],
        )