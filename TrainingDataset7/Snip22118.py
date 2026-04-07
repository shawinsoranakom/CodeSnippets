def test_conditional_expression_with_lookup(self):
        lookups = [
            Q(book__title__istartswith="poem"),
            Q(IStartsWith(F("book__title"), "poem")),
        ]
        for condition in lookups:
            with self.subTest(condition=condition):
                qs = Author.objects.annotate(
                    poem_book=FilteredRelation("book", condition=condition)
                ).filter(poem_book__isnull=False)
                self.assertSequenceEqual(qs, [self.author1])