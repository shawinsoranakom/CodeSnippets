def test_nested_subquery_join_outer_ref(self):
        inner = Employee.objects.filter(pk=OuterRef("ceo__pk")).values("pk")
        qs = Employee.objects.annotate(
            ceo_company=Subquery(
                Company.objects.filter(
                    ceo__in=inner,
                    ceo__pk=OuterRef("pk"),
                ).values("pk"),
            ),
        )
        self.assertSequenceEqual(
            qs.values_list("ceo_company", flat=True),
            [self.example_inc.pk, self.foobar_ltd.pk, self.gmbh.pk],
        )