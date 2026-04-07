def test_jsonb_agg_distinct_true(self):
        values = AggregateTestModel.objects.aggregate(
            jsonbagg=JSONBAgg("char_field", distinct=True),
        )
        self.assertEqual(sorted(values["jsonbagg"]), ["Bar", "Foo"])