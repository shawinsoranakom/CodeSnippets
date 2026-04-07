def test_lookup_decimal_larger_than_max_digits(self):
        self.assertSequenceEqual(Foo.objects.filter(d__lte=Decimal("123456")), [])