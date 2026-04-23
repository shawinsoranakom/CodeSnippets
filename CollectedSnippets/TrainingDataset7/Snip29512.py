def test_jsonb_agg_distinct_false(self):
        values = AggregateTestModel.objects.aggregate(
            jsonbagg=JSONBAgg("char_field", distinct=False),
        )
        self.assertEqual(sorted(values["jsonbagg"]), ["Bar", "Foo", "Foo"])