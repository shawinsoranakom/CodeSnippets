def test_year_lte(self):
        baseqs = Author.objects.order_by("name")
        self.assertSequenceEqual(
            baseqs.filter(birthdate__testyear__lte=2012),
            [self.a1, self.a2, self.a3, self.a4],
        )
        self.assertSequenceEqual(
            baseqs.filter(birthdate__testyear=2012), [self.a2, self.a3, self.a4]
        )

        self.assertNotIn("BETWEEN", str(baseqs.filter(birthdate__testyear=2012).query))
        self.assertSequenceEqual(
            baseqs.filter(birthdate__testyear__lte=2011), [self.a1]
        )
        # The non-optimized version works, too.
        self.assertSequenceEqual(baseqs.filter(birthdate__testyear__lt=2012), [self.a1])