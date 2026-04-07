def test_bit_xor_general(self):
        AggregateTestModel.objects.create(integer_field=3)
        values = AggregateTestModel.objects.filter(
            integer_field__in=[1, 3],
        ).aggregate(bitxor=BitXor("integer_field"))
        self.assertEqual(values, {"bitxor": 2})