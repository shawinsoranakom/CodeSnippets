def test_large_integer_precision_aggregation(self):
        large_int_val = Decimal("9999999999999999")
        BigD.objects.create(large_int=large_int_val, d=Decimal("0"))
        result = BigD.objects.aggregate(max_val=Max("large_int"))
        self.assertEqual(result["max_val"], large_int_val)