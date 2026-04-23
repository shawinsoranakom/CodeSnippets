def test_array_agg_filter_index(self):
        aggr1 = AggregateTestModel.objects.create(integer_field=1)
        aggr2 = AggregateTestModel.objects.create(integer_field=2)
        StatTestModel.objects.bulk_create(
            [
                StatTestModel(related_field=aggr1, int1=1, int2=0),
                StatTestModel(related_field=aggr1, int1=2, int2=1),
                StatTestModel(related_field=aggr2, int1=3, int2=0),
                StatTestModel(related_field=aggr2, int1=4, int2=1),
            ]
        )
        qs = (
            AggregateTestModel.objects.filter(pk__in=[aggr1.pk, aggr2.pk])
            .annotate(
                array=ArrayAgg("stattestmodel__int1", filter=Q(stattestmodel__int2=0))
            )
            .annotate(array_value=F("array__0"))
            .values_list("array_value", flat=True)
        )
        self.assertCountEqual(qs, [1, 3])