def test_bool_and_general(self):
        values = AggregateTestModel.objects.aggregate(booland=BoolAnd("boolean_field"))
        self.assertEqual(values, {"booland": False})