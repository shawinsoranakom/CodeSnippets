def test_conditional_expression(self):
        qs = Author.objects.annotate(
            the_book=FilteredRelation("book", condition=Q(Value(False))),
        ).filter(the_book__isnull=False)
        self.assertSequenceEqual(qs, [])