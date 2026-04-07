def test_join_promotion_multiple_annotations(self):
        o = CaseTestModel.objects.create(integer=1, integer2=1, string="1")
        # Testing that:
        # 1. There isn't any object on the remote side of the fk_rel
        #    relation. If the query used inner joins, then the join to fk_rel
        #    would remove o from the results. So, in effect we are testing that
        #    we are promoting the fk_rel join to a left outer join here.
        # 2. The default value of 3 is generated for the case expression.
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(pk=o.pk).annotate(
                foo=Case(
                    When(fk_rel__pk=1, then=2),
                    default=3,
                ),
                bar=Case(
                    When(fk_rel__pk=1, then=4),
                    default=5,
                ),
            ),
            [(o, 3, 5)],
            lambda x: (x, x.foo, x.bar),
        )
        # Now 2 should be generated, as the fk_rel is null.
        self.assertQuerySetEqual(
            CaseTestModel.objects.filter(pk=o.pk).annotate(
                foo=Case(
                    When(fk_rel__isnull=True, then=2),
                    default=3,
                ),
                bar=Case(
                    When(fk_rel__isnull=True, then=4),
                    default=5,
                ),
            ),
            [(o, 2, 4)],
            lambda x: (x, x.foo, x.bar),
        )