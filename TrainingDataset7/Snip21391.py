def test_outerref_with_operator(self):
        inner = Company.objects.filter(num_employees=OuterRef("ceo__salary") + 2)
        outer = Company.objects.filter(pk__in=Subquery(inner.values("pk")))
        self.assertEqual(outer.get().name, "Test GmbH")