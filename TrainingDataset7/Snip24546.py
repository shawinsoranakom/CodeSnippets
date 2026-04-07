def test_model_creation(self):
        """
        Test RasterField through a test model.
        """
        # Create model instance from JSON raster
        r = RasterModel.objects.create(rast=JSON_RASTER)
        r.refresh_from_db()
        # Test raster metadata properties
        self.assertEqual((5, 5), (r.rast.width, r.rast.height))
        self.assertEqual([0.0, -1.0, 0.0, 0.0, 0.0, 1.0], r.rast.geotransform)
        self.assertIsNone(r.rast.bands[0].nodata_value)
        # Compare srs
        self.assertEqual(r.rast.srs.srid, 4326)
        # Compare pixel values
        band = r.rast.bands[0].data()
        # If numpy, convert result to list
        if numpy:
            band = band.flatten().tolist()
        # Loop through rows in band data and assert single
        # value is as expected.
        self.assertEqual(
            [
                0.0,
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                9.0,
                10.0,
                11.0,
                12.0,
                13.0,
                14.0,
                15.0,
                16.0,
                17.0,
                18.0,
                19.0,
                20.0,
                21.0,
                22.0,
                23.0,
                24.0,
            ],
            band,
        )