def test_distinct_on_in_ordered_subquery(self):
        qs = Staff.objects.distinct("name").order_by("name", "id")
        qs = Staff.objects.filter(pk__in=qs).order_by("name")
        self.assertSequenceEqual(qs, [self.p1_o1, self.p2_o1, self.p3_o1])
        qs = Staff.objects.distinct("name").order_by("name", "-id")
        qs = Staff.objects.filter(pk__in=qs).order_by("name")
        self.assertSequenceEqual(qs, [self.p1_o2, self.p2_o1, self.p3_o1])