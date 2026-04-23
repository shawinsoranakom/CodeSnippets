def test_ticket17424(self):
        """
        Doing exclude() on a foreign model after annotate() doesn't crash.
        """
        all_books = list(Book.objects.values_list("pk", flat=True).order_by("pk"))
        annotated_books = Book.objects.order_by("pk").annotate(one=Count("id"))

        # The value doesn't matter, we just need any negative
        # constraint on a related model that's a noop.
        excluded_books = annotated_books.exclude(publisher__name="__UNLIKELY_VALUE__")

        # Try to generate query tree
        str(excluded_books.query)

        self.assertQuerySetEqual(excluded_books, all_books, lambda x: x.pk)

        # Check internal state
        self.assertIsNone(annotated_books.query.alias_map["aggregation_book"].join_type)
        self.assertIsNone(excluded_books.query.alias_map["aggregation_book"].join_type)