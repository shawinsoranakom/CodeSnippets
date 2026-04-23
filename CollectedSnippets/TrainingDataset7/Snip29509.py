def setUpTestData(cls):
        AggregateTestModel.objects.create(char_field="Foo")
        AggregateTestModel.objects.create(char_field="Foo")
        AggregateTestModel.objects.create(char_field="Bar")