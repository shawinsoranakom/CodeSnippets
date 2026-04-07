def test_bit_xor_on_only_false_values(self):
        values = AggregateTestModel.objects.filter(
            integer_field=0,
        ).aggregate(bitxor=BitXor("integer_field"))
        self.assertEqual(values, {"bitxor": 0})