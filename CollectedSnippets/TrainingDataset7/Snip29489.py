def test_bit_xor_on_only_true_values(self):
        values = AggregateTestModel.objects.filter(
            integer_field=1,
        ).aggregate(bitxor=BitXor("integer_field"))
        self.assertEqual(values, {"bitxor": 1})