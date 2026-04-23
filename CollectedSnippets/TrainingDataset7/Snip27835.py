def test_large_integer_precision(self):
        large_int_val = Decimal("9999999999999999")
        obj = BigD.objects.create(large_int=large_int_val, d=Decimal("0"))
        obj.refresh_from_db()
        self.assertEqual(obj.large_int, large_int_val)