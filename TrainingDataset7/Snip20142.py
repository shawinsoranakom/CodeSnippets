def test_birthdate_month(self):
        a1 = Author.objects.create(name="a1", birthdate=date(1981, 2, 16))
        a2 = Author.objects.create(name="a2", birthdate=date(2012, 2, 29))
        a3 = Author.objects.create(name="a3", birthdate=date(2012, 1, 31))
        a4 = Author.objects.create(name="a4", birthdate=date(2012, 3, 1))
        with register_lookup(models.DateField, InMonth):
            self.assertSequenceEqual(
                Author.objects.filter(birthdate__inmonth=date(2012, 1, 15)), [a3]
            )
            self.assertSequenceEqual(
                Author.objects.filter(birthdate__inmonth=date(2012, 2, 1)), [a2]
            )
            self.assertSequenceEqual(
                Author.objects.filter(birthdate__inmonth=date(1981, 2, 28)), [a1]
            )
            self.assertSequenceEqual(
                Author.objects.filter(birthdate__inmonth=date(2012, 3, 12)), [a4]
            )
            self.assertSequenceEqual(
                Author.objects.filter(birthdate__inmonth=date(2012, 4, 1)), []
            )