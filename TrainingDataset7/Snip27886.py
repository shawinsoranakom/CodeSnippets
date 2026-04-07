def test_callable_default(self):
        """A lazy callable may be used for ForeignKey.default."""
        a = Foo.objects.create(id=1, a="abc", d=Decimal("12.34"))
        b = Bar.objects.create(b="bcd")
        self.assertEqual(b.a, a)