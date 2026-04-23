def test_array_agg_charfield(self):
        values = AggregateTestModel.objects.aggregate(arrayagg=ArrayAgg("char_field"))
        self.assertEqual(values, {"arrayagg": ["Foo1", "Foo2", "Foo4", "Foo3"]})