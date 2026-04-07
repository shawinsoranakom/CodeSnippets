def test_filter_with_strings(self):
        """
        Should be able to filter decimal fields using strings (#8023).
        """
        foo = Foo.objects.create(a="abc", d=Decimal("12.34"))
        self.assertEqual(list(Foo.objects.filter(d="12.34")), [foo])