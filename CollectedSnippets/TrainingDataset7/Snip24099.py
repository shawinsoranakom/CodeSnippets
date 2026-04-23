def test_set_nodata_none_on_raster_creation(self):
        # Create raster without data and without nodata value.
        rast = GDALRaster(
            {
                "datatype": 1,
                "width": 2,
                "height": 2,
                "srid": 4326,
                "bands": [{"nodata_value": None}],
            }
        )
        # Get array from raster.
        result = rast.bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        # Band data is equal to zero because no nodata value has been
        # specified.
        self.assertEqual(result, [0] * 4)