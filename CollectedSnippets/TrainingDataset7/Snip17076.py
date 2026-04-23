def test_aggregates_in_where_clause_pre_eval(self):
        """
        Regression test for #12822: DatabaseError: aggregates not allowed in
        WHERE clause

        Same as the above test, but evaluates the queryset for the subquery
        before it's used as a subquery.

        Before the corresponding fix for this bug, this test failed in both
        1.1 and 1.2-beta (trunk).
        """
        qs = Book.objects.values("contact").annotate(Max("id"))
        qs = qs.order_by("contact").values_list("id__max", flat=True)
        # force the queryset (qs) for the subquery to be evaluated in its
        # current state
        list(qs)
        books = Book.objects.order_by("id")
        qs1 = books.filter(id__in=qs)
        qs2 = books.filter(id__in=list(qs))
        self.assertEqual(list(qs1), list(qs2))