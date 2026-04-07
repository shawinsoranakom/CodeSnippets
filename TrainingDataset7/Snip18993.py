def test_zero_as_autoval(self):
        """
        Zero as id for AutoField should raise exception in MySQL, because MySQL
        does not allow zero for automatic primary key if the
        NO_AUTO_VALUE_ON_ZERO SQL mode is not enabled.
        """
        valid_country = Country(name="Germany", iso_two_letter="DE")
        invalid_country = Country(id=0, name="Poland", iso_two_letter="PL")
        msg = "The database backend does not accept 0 as a value for AutoField."
        with self.assertRaisesMessage(ValueError, msg):
            Country.objects.bulk_create([valid_country, invalid_country])