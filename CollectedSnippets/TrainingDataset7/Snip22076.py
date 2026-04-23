def test_internal_queryset_alias_mapping(self):
        queryset = Author.objects.annotate(
            book_alice=FilteredRelation(
                "book", condition=Q(book__title__iexact="poem by alice")
            ),
        ).filter(book_alice__isnull=False)
        self.assertIn(
            "INNER JOIN {} {} ON".format(
                connection.ops.quote_name("filtered_relation_book"),
                connection.ops.quote_name("book_alice"),
            ),
            str(queryset.query),
        )