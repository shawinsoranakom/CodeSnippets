def test_conditional_expression_does_not_support_queryset(self):
        msg = "Passing a QuerySet within a FilteredRelation is not supported."
        with self.assertRaisesMessage(ValueError, msg):
            Author.objects.annotate(
                poem_book=FilteredRelation(
                    "book",
                    condition=Q(book__in=Book.objects.filter(title__istartswith="a")),
                ),
            ).filter(poem_book__isnull=False)