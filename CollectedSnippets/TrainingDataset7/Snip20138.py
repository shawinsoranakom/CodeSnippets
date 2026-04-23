def test_custom_name_lookup(self):
        a1 = Author.objects.create(name="a1", birthdate=date(1981, 2, 16))
        Author.objects.create(name="a2", birthdate=date(2012, 2, 29))
        with (
            register_lookup(models.DateField, YearTransform),
            register_lookup(models.DateField, YearTransform, lookup_name="justtheyear"),
            register_lookup(YearTransform, Exactly),
            register_lookup(YearTransform, Exactly, lookup_name="isactually"),
        ):
            qs1 = Author.objects.filter(birthdate__testyear__exactly=1981)
            qs2 = Author.objects.filter(birthdate__justtheyear__isactually=1981)
            self.assertSequenceEqual(qs1, [a1])
            self.assertSequenceEqual(qs2, [a1])