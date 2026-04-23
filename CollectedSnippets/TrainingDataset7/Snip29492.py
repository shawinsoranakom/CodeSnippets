def test_bool_and_q_object(self):
        values = AggregateTestModel.objects.aggregate(
            booland=BoolAnd(Q(integer_field__gt=2)),
        )
        self.assertEqual(values, {"booland": False})