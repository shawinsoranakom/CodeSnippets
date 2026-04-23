def test_basic_distinct_on(self):
        """QuerySet.distinct('field', ...) works"""
        # (qset, expected) tuples
        qsets = (
            (
                Staff.objects.distinct().order_by("name"),
                [self.p1_o1, self.p1_o2, self.p2_o1, self.p3_o1],
            ),
            (
                Staff.objects.distinct("name").order_by("name"),
                [self.p1_o1, self.p2_o1, self.p3_o1],
            ),
            (
                Staff.objects.distinct("organisation").order_by("organisation", "name"),
                [self.p1_o1, self.p1_o2],
            ),
            (
                Staff.objects.distinct("name", "organisation").order_by(
                    "name", "organisation"
                ),
                [self.p1_o1, self.p1_o2, self.p2_o1, self.p3_o1],
            ),
            (
                Celebrity.objects.filter(fan__in=[self.fan1, self.fan2, self.fan3])
                .distinct("name")
                .order_by("name"),
                [self.celeb1, self.celeb2],
            ),
            # Does combining querysets work?
            (
                (
                    Celebrity.objects.filter(fan__in=[self.fan1, self.fan2])
                    .distinct("name")
                    .order_by("name")
                    | Celebrity.objects.filter(fan__in=[self.fan3])
                    .distinct("name")
                    .order_by("name")
                ),
                [self.celeb1, self.celeb2],
            ),
            (StaffTag.objects.distinct("staff", "tag"), [self.st1]),
            (
                Tag.objects.order_by("parent__pk", "pk").distinct("parent"),
                (
                    [self.t2, self.t4, self.t1]
                    if connection.features.nulls_order_largest
                    else [self.t1, self.t2, self.t4]
                ),
            ),
            (
                StaffTag.objects.select_related("staff")
                .distinct("staff__name")
                .order_by("staff__name"),
                [self.st1],
            ),
            # Fetch the alphabetically first coworker for each worker
            (
                (
                    Staff.objects.distinct("id")
                    .order_by("id", "coworkers__name")
                    .values_list("id", "coworkers__name")
                ),
                [(1, "p2"), (2, "p1"), (3, "p1"), (4, None)],
            ),
        )
        for qset, expected in qsets:
            self.assertSequenceEqual(qset, expected)
            self.assertEqual(qset.count(), len(expected))

        # Combining queries with non-unique query is not allowed.
        base_qs = Celebrity.objects.all()
        msg = "Cannot combine a unique query with a non-unique query."
        with self.assertRaisesMessage(TypeError, msg):
            base_qs.distinct("id") & base_qs
        # Combining queries with different distinct_fields is not allowed.
        msg = "Cannot combine queries with different distinct fields."
        with self.assertRaisesMessage(TypeError, msg):
            base_qs.distinct("id") & base_qs.distinct("name")

        # Test join unreffing
        c1 = Celebrity.objects.distinct("greatest_fan__id", "greatest_fan__fan_of")
        self.assertIn("OUTER JOIN", str(c1.query))
        c2 = c1.distinct("pk")
        self.assertNotIn("OUTER JOIN", str(c2.query))