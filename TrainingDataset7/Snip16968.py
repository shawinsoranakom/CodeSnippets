def test_ticket11881(self):
        """
        Subqueries do not needlessly contain ORDER BY, SELECT FOR UPDATE or
        select_related() stuff.
        """
        qs = (
            Book.objects.select_for_update()
            .order_by("pk")
            .select_related("publisher")
            .annotate(max_pk=Max("pk"))
        )
        with CaptureQueriesContext(connection) as captured_queries:
            qs.aggregate(avg_pk=Avg("max_pk"))
            self.assertEqual(len(captured_queries), 1)
            qstr = captured_queries[0]["sql"].lower()
            self.assertNotIn("for update", qstr)
            forced_ordering = connection.ops.force_no_ordering()
            if forced_ordering:
                # If the backend needs to force an ordering we make sure it's
                # the only "ORDER BY" clause present in the query.
                self.assertEqual(
                    re.findall(r"order by (\w+)", qstr),
                    [", ".join(f[1][0] for f in forced_ordering).lower()],
                )
            else:
                self.assertNotIn("order by", qstr)
            self.assertEqual(qstr.count(" join "), 0)