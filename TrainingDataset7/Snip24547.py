def test_implicit_raster_transformation(self):
        """
        Test automatic transformation of rasters with srid different from the
        field srid.
        """
        # Parse json raster
        rast = json.loads(JSON_RASTER)
        # Update srid to another value
        rast["srid"] = 3086
        # Save model and get it from db
        r = RasterModel.objects.create(rast=rast)
        r.refresh_from_db()
        # Confirm raster has been transformed to the default srid
        self.assertEqual(r.rast.srs.srid, 4326)
        # Confirm geotransform is in lat/lon
        expected = [
            -87.9298551266551,
            9.459646421449934e-06,
            0.0,
            23.94249275457565,
            0.0,
            -9.459646421449934e-06,
        ]
        for val, exp in zip(r.rast.geotransform, expected):
            self.assertAlmostEqual(exp, val)