def test_nested_foreign_key_nested_field(self):
        qs = (
            Author.objects.annotate(
                book_editor_worked_with=FilteredRelation(
                    "book__editor", condition=Q(book__title__icontains="book by")
                ),
            )
            .filter(
                book_editor_worked_with__isnull=False,
            )
            .values(
                "name",
                "book_editor_worked_with__name",
            )
            .order_by("name", "book_editor_worked_with__name")
            .distinct()
        )
        self.assertSequenceEqual(
            qs,
            [
                {
                    "name": self.author1.name,
                    "book_editor_worked_with__name": self.editor_a.name,
                },
                {
                    "name": self.author2.name,
                    "book_editor_worked_with__name": self.editor_b.name,
                },
            ],
        )