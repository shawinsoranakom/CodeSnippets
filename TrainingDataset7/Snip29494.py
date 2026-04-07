def test_bool_or_q_object(self):
        values = AggregateTestModel.objects.aggregate(
            boolor=BoolOr(Q(integer_field__gt=2)),
        )
        self.assertEqual(values, {"boolor": False})