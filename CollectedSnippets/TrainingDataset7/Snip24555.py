def test_isvalid_lookup_with_raster_error(self):
        qs = RasterModel.objects.filter(rast__isvalid=True)
        msg = (
            "IsValid function requires a GeometryField in position 1, got RasterField."
        )
        with self.assertRaisesMessage(TypeError, msg):
            qs.count()