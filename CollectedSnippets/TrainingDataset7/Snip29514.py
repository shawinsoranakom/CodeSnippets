def setUpTestData(cls):
        StatTestModel.objects.create(
            int1=1,
            int2=3,
            related_field=AggregateTestModel.objects.create(integer_field=0),
        )
        StatTestModel.objects.create(
            int1=2,
            int2=2,
            related_field=AggregateTestModel.objects.create(integer_field=1),
        )
        StatTestModel.objects.create(
            int1=3,
            int2=1,
            related_field=AggregateTestModel.objects.create(integer_field=2),
        )