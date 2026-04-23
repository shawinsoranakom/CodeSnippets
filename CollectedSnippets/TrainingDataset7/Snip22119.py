def test_conditional_expression_with_expressionwrapper(self):
        qs = Author.objects.annotate(
            poem_book=FilteredRelation(
                "book",
                condition=Q(
                    ExpressionWrapper(
                        Q(Exact(F("book__title"), "Poem by Alice")),
                        output_field=BooleanField(),
                    ),
                ),
            ),
        ).filter(poem_book__isnull=False)
        self.assertSequenceEqual(qs, [self.author1])