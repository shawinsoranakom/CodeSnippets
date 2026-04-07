def test_group_by_field_uniqueness(self):
        # Regression for #15709 - Ensure each group_by field only exists once
        # per query
        qstr = str(
            Book.objects.values("publisher")
            .annotate(max_pages=Max("pages"))
            .order_by()
            .query
        )
        # There is just one GROUP BY clause (zero commas means at most one
        # clause).
        self.assertEqual(qstr[qstr.index("GROUP BY") :].count(", "), 0)