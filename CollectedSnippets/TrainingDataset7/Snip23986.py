def test_measurement_null_fields(self):
        """
        Test the measurement functions on fields with NULL values.
        """
        # Creating SouthTexasZipcode w/NULL value.
        SouthTexasZipcode.objects.create(name="78212")
        # Performing distance/area queries against the NULL PolygonField,
        # and ensuring the result of the operations is None.
        htown = SouthTexasCity.objects.get(name="Downtown Houston")
        z = SouthTexasZipcode.objects.annotate(
            distance=Distance("poly", htown.point), area=Area("poly")
        ).get(name="78212")
        self.assertIsNone(z.distance)
        self.assertIsNone(z.area)