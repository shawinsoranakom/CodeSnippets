def test_values_list_annotation_args_ordering(self):
        """
        Annotate *args ordering should be preserved in values_list results.
        **kwargs comes after *args.
        Regression test for #23659.
        """
        books = (
            Book.objects.values_list("publisher__name")
            .annotate(
                Count("id"), Avg("price"), Avg("authors__age"), avg_pgs=Avg("pages")
            )
            .order_by("-publisher__name")
        )
        self.assertEqual(books[0], ("Sams", 1, Decimal("23.09"), 45.0, 528.0))