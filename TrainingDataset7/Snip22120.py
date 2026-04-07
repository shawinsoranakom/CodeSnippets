def test_conditional_expression_with_multiple_fields(self):
        qs = Author.objects.annotate(
            my_books=FilteredRelation(
                "book__author",
                condition=Q(Exact(F("book__author__name"), F("book__author__name"))),
            ),
        ).filter(my_books__isnull=True)
        self.assertSequenceEqual(qs, [])