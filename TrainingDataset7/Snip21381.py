def test_nested_subquery_outer_ref_with_autofield(self):
        first = Time.objects.create(time="09:00")
        second = Time.objects.create(time="17:00")
        SimulationRun.objects.create(start=first, end=second, midpoint="12:00")
        inner = SimulationRun.objects.filter(start=OuterRef(OuterRef("pk"))).values(
            "start"
        )
        middle = Time.objects.annotate(other=Subquery(inner)).values("other")[:1]
        outer = Time.objects.annotate(
            other=Subquery(middle, output_field=IntegerField())
        )
        # This exercises the double OuterRef form with AutoField as pk.
        self.assertCountEqual(outer, [first, second])