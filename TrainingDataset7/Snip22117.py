def test_conditional_expression_outside_relation_name(self):
        tests = [
            Q(Case(When(book__author__name="Alice", then=True), default=False)),
            Q(
                ExpressionWrapper(
                    Q(Value(True), Exact(F("book__author__name"), "Alice")),
                    output_field=BooleanField(),
                ),
            ),
        ]
        for condition in tests:
            with self.subTest(condition=condition):
                qs = Author.objects.annotate(
                    book_editor=FilteredRelation("book__editor", condition=condition),
                ).filter(book_editor__isnull=True)
                self.assertSequenceEqual(qs, [self.author2, self.author2])