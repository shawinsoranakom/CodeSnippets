def test_condition_with_lookups(self):
        qs = CaseTestModel.objects.annotate(
            test=Case(
                When(Q(integer2=1), string="2", then=Value(False)),
                When(Q(integer2=1), string="1", then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
        self.assertIs(qs.get(integer=1).test, True)