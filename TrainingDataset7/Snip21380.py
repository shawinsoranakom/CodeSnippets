def test_nested_subquery_outer_ref_2(self):
        first = Time.objects.create(time="09:00")
        second = Time.objects.create(time="17:00")
        third = Time.objects.create(time="21:00")
        SimulationRun.objects.bulk_create(
            [
                SimulationRun(start=first, end=second, midpoint="12:00"),
                SimulationRun(start=first, end=third, midpoint="15:00"),
                SimulationRun(start=second, end=first, midpoint="00:00"),
            ]
        )
        inner = Time.objects.filter(
            time=OuterRef(OuterRef("time")), pk=OuterRef("start")
        ).values("time")
        middle = SimulationRun.objects.annotate(other=Subquery(inner)).values("other")[
            :1
        ]
        outer = Time.objects.annotate(other=Subquery(middle, output_field=TimeField()))
        # This is a contrived example. It exercises the double OuterRef form.
        self.assertCountEqual(outer, [first, second, third])