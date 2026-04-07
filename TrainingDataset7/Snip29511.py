def test_array_agg_distinct_true(self):
        values = AggregateTestModel.objects.aggregate(
            arrayagg=ArrayAgg("char_field", distinct=True)
        )
        self.assertEqual(sorted(values["arrayagg"]), ["Bar", "Foo"])