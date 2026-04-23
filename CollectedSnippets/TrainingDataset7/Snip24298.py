def test_geography_unique(self):
        """
        Cast geography fields to geometry type when validating uniqueness to
        remove the reliance on unavailable ~= operator.
        """
        htown = City.objects.get(name="Houston")
        CityUnique.objects.create(point=htown.point)
        duplicate = CityUnique(point=htown.point)
        msg = "City unique with this Point already exists."
        with self.assertRaisesMessage(ValidationError, msg):
            duplicate.validate_unique()