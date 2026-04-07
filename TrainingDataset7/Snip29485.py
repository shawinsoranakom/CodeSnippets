def test_bit_or_general(self):
        values = AggregateTestModel.objects.filter(integer_field__in=[0, 1]).aggregate(
            bitor=BitOr("integer_field")
        )
        self.assertEqual(values, {"bitor": 1})