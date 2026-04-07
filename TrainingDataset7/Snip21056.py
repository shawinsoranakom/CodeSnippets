def test_resolve_columns(self):
        ResolveThis.objects.create(num=5.0, name="Foobar")
        qs = ResolveThis.objects.defer("num")
        self.assertEqual(1, qs.count())
        self.assertEqual("Foobar", qs[0].name)