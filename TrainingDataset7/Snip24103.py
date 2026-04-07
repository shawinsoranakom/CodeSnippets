def test_raster_warp(self):
        # Create in memory raster
        source = GDALRaster(
            {
                "datatype": 1,
                "driver": "MEM",
                "name": "sourceraster",
                "width": 4,
                "height": 4,
                "nr_of_bands": 1,
                "srid": 3086,
                "origin": (500000, 400000),
                "scale": (100, -100),
                "skew": (0, 0),
                "bands": [
                    {
                        "data": range(16),
                        "nodata_value": 255,
                    }
                ],
            }
        )

        # Test altering the scale, width, and height of a raster
        data = {
            "scale": [200, -200],
            "width": 2,
            "height": 2,
        }
        target = source.warp(data)
        self.assertEqual(target.width, data["width"])
        self.assertEqual(target.height, data["height"])
        self.assertEqual(target.scale, data["scale"])
        self.assertEqual(target.bands[0].datatype(), source.bands[0].datatype())
        self.assertEqual(target.name, "sourceraster_copy.MEM")
        result = target.bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        self.assertEqual(result, [5, 7, 13, 15])

        # Test altering the name and datatype (to float)
        data = {
            "name": "/path/to/targetraster.tif",
            "datatype": 6,
        }
        target = source.warp(data)
        self.assertEqual(target.bands[0].datatype(), 6)
        self.assertEqual(target.name, "/path/to/targetraster.tif")
        self.assertEqual(target.driver.name, "MEM")
        result = target.bands[0].data()
        if numpy:
            result = result.flatten().tolist()
        self.assertEqual(
            result,
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
            ],
        )