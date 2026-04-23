def test_jsonb_agg(self):
        values = AggregateTestModel.objects.aggregate(jsonbagg=JSONBAgg("char_field"))
        self.assertEqual(values, {"jsonbagg": ["Foo1", "Foo2", "Foo4", "Foo3"]})