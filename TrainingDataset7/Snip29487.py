def test_bit_or_on_only_false_values(self):
        values = AggregateTestModel.objects.filter(integer_field=0).aggregate(
            bitor=BitOr("integer_field")
        )
        self.assertEqual(values, {"bitor": 0})