def test_condition_with_exact_lookup_outside_relation_name(self):
        qs = Author.objects.annotate(
            book_editor=FilteredRelation(
                "book__editor",
                condition=Q(book__author__name="book"),
            ),
        ).filter(book_editor__isnull=True)
        self.assertEqual(qs.count(), 4)