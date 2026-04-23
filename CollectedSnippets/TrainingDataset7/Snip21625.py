def test_m2m_reuse(self):
        CaseTestModel.objects.create(integer=10, integer2=1, string="1")
        # Need to use values before annotate so that Oracle will not group
        # by fields it isn't capable of grouping by.
        qs = (
            CaseTestModel.objects.values_list("id", "integer")
            .annotate(
                cnt=Sum(
                    Case(When(~Q(fk_rel__integer=1), then=1), default=2),
                ),
            )
            .annotate(
                cnt2=Sum(
                    Case(When(~Q(fk_rel__integer=1), then=1), default=2),
                ),
            )
            .order_by("integer")
        )
        self.assertEqual(str(qs.query).count(" JOIN "), 1)
        self.assertQuerySetEqual(
            qs,
            [
                (1, 2, 2),
                (2, 2, 2),
                (2, 2, 2),
                (3, 2, 2),
                (3, 2, 2),
                (3, 2, 2),
                (4, 1, 1),
                (10, 1, 1),
            ],
            lambda x: x[1:],
        )