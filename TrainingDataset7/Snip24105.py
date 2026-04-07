def test_raster_clone(self):
        rstfile = NamedTemporaryFile(suffix=".tif")
        tests = [
            ("MEM", "", 23),  # In memory raster.
            ("tif", rstfile.name, 99),  # In file based raster.
        ]
        for driver, name, nodata_value in tests:
            with self.subTest(driver=driver):
                source = GDALRaster(
                    {
                        "datatype": 1,
                        "driver": driver,
                        "name": name,
                        "width": 4,
                        "height": 4,
                        "srid": 3086,
                        "origin": (500000, 400000),
                        "scale": (100, -100),
                        "skew": (0, 0),
                        "bands": [
                            {
                                "data": range(16),
                                "nodata_value": nodata_value,
                            }
                        ],
                    }
                )
                clone = source.clone()
                self.assertNotEqual(clone.name, source.name)
                self.assertEqual(clone._write, source._write)
                self.assertEqual(clone.srs.srid, source.srs.srid)
                self.assertEqual(clone.width, source.width)
                self.assertEqual(clone.height, source.height)
                self.assertEqual(clone.origin, source.origin)
                self.assertEqual(clone.scale, source.scale)
                self.assertEqual(clone.skew, source.skew)
                self.assertIsNot(clone, source)