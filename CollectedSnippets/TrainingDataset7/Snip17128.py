def test_filtering_by_annotation_name(self):
        # Regression test for #14476

        # The name of the explicitly provided annotation name in this case
        # poses no problem
        qs = (
            Author.objects.annotate(book_cnt=Count("book"))
            .filter(book_cnt=2)
            .order_by("name")
        )
        self.assertQuerySetEqual(qs, ["Peter Norvig"], lambda b: b.name)
        # Neither in this case
        qs = (
            Author.objects.annotate(book_count=Count("book"))
            .filter(book_count=2)
            .order_by("name")
        )
        self.assertQuerySetEqual(qs, ["Peter Norvig"], lambda b: b.name)
        # This case used to fail because the ORM couldn't resolve the
        # automatically generated annotation name `book__count`
        qs = (
            Author.objects.annotate(Count("book"))
            .filter(book__count=2)
            .order_by("name")
        )
        self.assertQuerySetEqual(qs, ["Peter Norvig"], lambda b: b.name)
        # Referencing the auto-generated name in an aggregate() also works.
        self.assertEqual(
            Author.objects.annotate(Count("book")).aggregate(Max("book__count")),
            {"book__count__max": 2},
        )