def test_nested_foreign_key(self):
        qs = (
            Author.objects.annotate(
                book_editor_worked_with=FilteredRelation(
                    "book__editor",
                    condition=Q(book__title__icontains="book by"),
                ),
            )
            .filter(
                book_editor_worked_with__isnull=False,
            )
            .select_related(
                "book_editor_worked_with",
            )
            .order_by("pk", "book_editor_worked_with__pk")
        )
        with self.assertNumQueries(1):
            self.assertQuerySetEqual(
                qs,
                [
                    (self.author1, self.editor_a),
                    (self.author2, self.editor_b),
                    (self.author2, self.editor_b),
                ],
                lambda x: (x, x.book_editor_worked_with),
            )