def test_F_reuse(self):
        f = F("id")
        n = Number.objects.create(integer=-1)
        c = Company.objects.create(
            name="Example Inc.",
            num_employees=2300,
            num_chairs=5,
            ceo=Employee.objects.create(firstname="Joe", lastname="Smith"),
        )
        c_qs = Company.objects.filter(id=f)
        self.assertEqual(c_qs.get(), c)
        # Reuse the same F-object for another queryset
        n_qs = Number.objects.filter(id=f)
        self.assertEqual(n_qs.get(), n)
        # The original query still works correctly
        self.assertEqual(c_qs.get(), c)