def test_memory_based_raster_creation(self):
        # Create uint8 raster with full pixel data range (0-255)
        rast = GDALRaster(
            {
                "datatype": 1,
                "width": 16,
                "height": 16,
                "srid": 4326,
                "bands": [
                    {
                        "data": range(256),
                        "nodata_value": 255,
                    }
                ],
            }
        )

        # Get array from raster
        result = rast.bands[0].data()
        if numpy:
            result = result.flatten().tolist()

        # Assert data is same as original input
        self.assertEqual(result, list(range(256)))