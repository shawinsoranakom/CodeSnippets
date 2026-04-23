def test_year_lte_fexpr(self):
        self.a2.age = 2011
        self.a2.save()
        self.a3.age = 2012
        self.a3.save()
        self.a4.age = 2013
        self.a4.save()
        baseqs = Author.objects.order_by("name")
        self.assertSequenceEqual(
            baseqs.filter(birthdate__testyear__lte=models.F("age")), [self.a3, self.a4]
        )
        self.assertSequenceEqual(
            baseqs.filter(birthdate__testyear__lt=models.F("age")), [self.a4]
        )