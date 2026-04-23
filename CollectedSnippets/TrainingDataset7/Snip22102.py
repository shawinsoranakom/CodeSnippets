def test_deep_nested_foreign_key(self):
        qs = (
            Book.objects.annotate(
                author_favorite_book_editor=FilteredRelation(
                    "author__favorite_books__editor",
                    condition=Q(author__favorite_books__title__icontains="Jane A"),
                ),
            )
            .filter(
                author_favorite_book_editor__isnull=False,
            )
            .select_related(
                "author_favorite_book_editor",
            )
            .order_by("pk", "author_favorite_book_editor__pk")
        )
        with self.assertNumQueries(1):
            self.assertQuerySetEqual(
                qs,
                [
                    (self.book1, self.editor_b),
                    (self.book4, self.editor_b),
                ],
                lambda x: (x, x.author_favorite_book_editor),
            )