def test_field_null_value(self):
        """
        Test creating a model where the RasterField has a null value.
        """
        r = RasterModel.objects.create(rast=None)
        r.refresh_from_db()
        self.assertIsNone(r.rast)