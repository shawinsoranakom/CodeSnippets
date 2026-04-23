def test_raster_warp_nodata_zone(self):
        # Create in memory raster.
        source = GDALRaster(
            {
                "datatype": 1,
                "driver": "MEM",
                "width": 4,
                "height": 4,
                "srid": 3086,
                "origin": (500000, 400000),
                "scale": (100, -100),
                "skew": (0, 0),
                "bands": [
                    {
                        "data": range(16),
                        "nodata_value": 23,
                    }
                ],
            }
        )
        # Warp raster onto a location that does not cover any pixels of the
        # original.
        result = source.warp({"origin": (200000, 200000)}).bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        # The result is an empty raster filled with the correct nodata value.
        self.assertEqual(result, [23] * 16)