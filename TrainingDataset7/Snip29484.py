def test_bit_and_on_only_false_values(self):
        values = AggregateTestModel.objects.filter(integer_field=0).aggregate(
            bitand=BitAnd("integer_field")
        )
        self.assertEqual(values, {"bitand": 0})