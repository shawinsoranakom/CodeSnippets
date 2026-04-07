def test_m2m_exclude(self):
        CaseTestModel.objects.create(integer=10, integer2=1, string="1")
        qs = (
            CaseTestModel.objects.values_list("id", "integer")
            .annotate(
                cnt=Sum(
                    Case(When(~Q(fk_rel__integer=1), then=1), default=2),
                ),
            )
            .order_by("integer")
        )
        # The first o has 2 as its fk_rel__integer=1, thus it hits the
        # default=2 case. The other ones have 2 as the result as they have 2
        # fk_rel objects, except for integer=4 and integer=10 (created above).
        # The integer=4 case has one integer, thus the result is 1, and
        # integer=10 doesn't have any and this too generates 1 (instead of 0)
        # as ~Q() also matches nulls.
        self.assertQuerySetEqual(
            qs,
            [(1, 2), (2, 2), (2, 2), (3, 2), (3, 2), (3, 2), (4, 1), (10, 1)],
            lambda x: x[1:],
        )