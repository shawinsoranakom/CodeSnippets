def test_bit_and_general(self):
        values = AggregateTestModel.objects.filter(integer_field__in=[0, 1]).aggregate(
            bitand=BitAnd("integer_field")
        )
        self.assertEqual(values, {"bitand": 0})