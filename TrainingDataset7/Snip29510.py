def test_array_agg_distinct_false(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("char_field", distinct=False)
        )
        self.assertEqual(sorted(values["arrayagg"]), ["Bar", "Foo", "Foo"])