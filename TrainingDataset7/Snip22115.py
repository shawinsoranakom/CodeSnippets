def test_expression_outside_relation_name(self):
        qs = Author.objects.annotate(
            book_editor=FilteredRelation(
                "book__editor",
                condition=Q(
                    Exact(F("book__author__name"), "Alice"),
                    Value(True),
                    book__title__startswith="Poem",
                ),
            ),
        ).filter(book_editor__isnull=False)
        self.assertSequenceEqual(qs, [self.author1])