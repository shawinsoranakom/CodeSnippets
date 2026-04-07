def test_geotransform_bad_inputs(self):
        rsmem = GDALRaster(JSON_RASTER)
        error_geotransforms = [
            [1, 2],
            [1, 2, 3, 4, 5, "foo"],
            [1, 2, 3, 4, 5, 6, "foo"],
        ]
        msg = "Geotransform must consist of 6 numeric values."
        for geotransform in error_geotransforms:
            with (
                self.subTest(i=geotransform),
                self.assertRaisesMessage(ValueError, msg),
            ):
                rsmem.geotransform = geotransform