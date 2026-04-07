def test_bit_and_on_only_true_values(self):
        values = AggregateTestModel.objects.filter(integer_field=1).aggregate(
            bitand=BitAnd("integer_field")
        )
        self.assertEqual(values, {"bitand": 1})