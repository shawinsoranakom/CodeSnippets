def test_offset_size_and_shape_on_raster_creation(self):
        rast = GDALRaster(
            {
                "datatype": 1,
                "width": 4,
                "height": 4,
                "srid": 4326,
                "bands": [
                    {
                        "data": (1,),
                        "offset": (1, 1),
                        "size": (2, 2),
                        "shape": (1, 1),
                        "nodata_value": 2,
                    }
                ],
            }
        )
        # Get array from raster.
        result = rast.bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        # Band data is equal to nodata value except on input block of ones.
        self.assertEqual(result, [2, 2, 2, 2, 2, 1, 1, 2, 2, 1, 1, 2, 2, 2, 2, 2])