def test_lookup_value_error(self):
        # Test with invalid dict lookup parameter
        obj = {}
        msg = "Couldn't create spatial object from lookup value '%s'." % obj
        with self.assertRaisesMessage(ValueError, msg):
            RasterModel.objects.filter(geom__intersects=obj)
        # Test with invalid string lookup parameter
        obj = "00000"
        msg = "Couldn't create spatial object from lookup value '%s'." % obj
        with self.assertRaisesMessage(ValueError, msg):
            RasterModel.objects.filter(geom__intersects=obj)