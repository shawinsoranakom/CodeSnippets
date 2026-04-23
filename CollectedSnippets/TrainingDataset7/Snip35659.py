def test_order_by_update_on_related_field(self):
        # Ordering by related fields is omitted because joined fields cannot be
        # used in the ORDER BY clause.
        data = DataPoint.objects.create(name="d0", value="apple")
        related = RelatedPoint.objects.create(name="r0", data=data)
        with self.assertNumQueries(1) as ctx:
            updated = RelatedPoint.objects.order_by("data__name").update(name="new")
        sql = ctx.captured_queries[0]["sql"]
        self.assertNotIn("ORDER BY", sql)
        self.assertEqual(updated, 1)
        related.refresh_from_db()
        self.assertEqual(related.name, "new")