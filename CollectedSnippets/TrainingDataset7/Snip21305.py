def test_distinct_on_mixed_case_annotation(self):
        qs = (
            Staff.objects.annotate(
                nAmEAlIaS=F("name"),
            )
            .distinct("nAmEAlIaS")
            .order_by("nAmEAlIaS")
        )
        self.assertSequenceEqual(qs, [self.p1_o1, self.p2_o1, self.p3_o1])