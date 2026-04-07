def test_bool_or_general(self):
        values = AggregateTestModel.objects.aggregate(boolor=BoolOr("boolean_field"))
        self.assertEqual(values, {"boolor": True})