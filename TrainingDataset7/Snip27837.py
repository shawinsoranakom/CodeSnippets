def test_roundtrip_integer_with_trailing_zeros(self):
        obj = Foo.objects.create(a="bar", d=Decimal("8"))
        obj.refresh_from_db()
        self.assertEqual(obj.d.compare_total(Decimal("8.000")), Decimal("0"))