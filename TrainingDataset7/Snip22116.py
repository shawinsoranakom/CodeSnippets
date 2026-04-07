def test_conditional_expression_with_case(self):
        qs = Book.objects.annotate(
            alice_author=FilteredRelation(
                "author",
                condition=Q(
                    Case(When(author__name="Alice", then=True), default=False),
                ),
            ),
        ).filter(alice_author__isnull=False)
        self.assertCountEqual(qs, [self.book1, self.book4])