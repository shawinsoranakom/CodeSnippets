def setUpTestData(cls):
        cls.aggs = AggregateTestModel.objects.bulk_create(
            [
                AggregateTestModel(
                    boolean_field=True,
                    char_field="Foo1",
                    text_field="Text1",
                    integer_field=0,
                ),
                AggregateTestModel(
                    boolean_field=False,
                    char_field="Foo2",
                    text_field="Text2",
                    integer_field=1,
                    json_field={"lang": "pl"},
                ),
                AggregateTestModel(
                    boolean_field=False,
                    char_field="Foo4",
                    text_field="Text4",
                    integer_field=2,
                    json_field={"lang": "en"},
                ),
                AggregateTestModel(
                    boolean_field=True,
                    char_field="Foo3",
                    text_field="Text3",
                    integer_field=0,
                    json_field={"breed": "collie"},
                ),
            ]
        )