def test_condition_with_func_and_lookup_outside_relation_name(self):
        qs = Author.objects.annotate(
            book_editor=FilteredRelation(
                "book__editor",
                condition=Q(
                    book__title=Concat(Value("The book by "), F("book__author__name"))
                ),
            ),
        ).filter(book_editor__isnull=False)
        self.assertEqual(qs.count(), 1)