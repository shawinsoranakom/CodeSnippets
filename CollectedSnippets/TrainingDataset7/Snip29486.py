def test_bit_or_on_only_true_values(self):
        values = AggregateTestModel.objects.filter(integer_field=1).aggregate(
            bitor=BitOr("integer_field")
        )
        self.assertEqual(values, {"bitor": 1})