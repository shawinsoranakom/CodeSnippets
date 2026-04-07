def test_array_agg_lookups(self):
        aggr1 = AggregateTestModel.objects.create()
        aggr2 = AggregateTestModel.objects.create()
        StatTestModel.objects.create(related_field=aggr1, int1=1, int2=0)
        StatTestModel.objects.create(related_field=aggr1, int1=2, int2=0)
        StatTestModel.objects.create(related_field=aggr2, int1=3, int2=0)
        StatTestModel.objects.create(related_field=aggr2, int1=4, int2=0)
        qs = (
            StatTestModel.objects.values("related_field")
            .annotate(array=ArrayAgg("int1"))
            .filter(array__overlap=[2])
            .values_list("array", flat=True)
        )
        self.assertCountEqual(qs.get(), [1, 2])