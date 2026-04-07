def test_aggregates_in_where_clause(self):
        """
        Regression test for #12822: DatabaseError: aggregates not allowed in
        WHERE clause

        The subselect works and returns results equivalent to a
        query with the IDs listed.

        Before the corresponding fix for this bug, this test passed in 1.1 and
        failed in 1.2-beta (trunk).
        """
        qs = Book.objects.values("contact").annotate(Max("id"))
        qs = qs.order_by("contact").values_list("id__max", flat=True)
        # don't do anything with the queryset (qs) before including it as a
        # subquery
        books = Book.objects.order_by("id")
        qs1 = books.filter(id__in=qs)
        qs2 = books.filter(id__in=list(qs))
        self.assertEqual(list(qs1), list(qs2))