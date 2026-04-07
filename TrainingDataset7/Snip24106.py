def test_raster_transform(self):
        tests = [
            3086,
            "3086",
            SpatialReference(3086),
        ]
        for srs in tests:
            with self.subTest(srs=srs):
                # Prepare tempfile and nodata value.
                rstfile = NamedTemporaryFile(suffix=".tif")
                ndv = 99
                # Create in file based raster.
                source = GDALRaster(
                    {
                        "datatype": 1,
                        "driver": "tif",
                        "name": rstfile.name,
                        "width": 5,
                        "height": 5,
                        "nr_of_bands": 1,
                        "srid": 4326,
                        "origin": (-5, 5),
                        "scale": (2, -2),
                        "skew": (0, 0),
                        "bands": [
                            {
                                "data": range(25),
                                "nodata_value": ndv,
                            }
                        ],
                    }
                )

                target = source.transform(srs)

                # Reload data from disk.
                target = GDALRaster(target.name)
                self.assertEqual(target.srs.srid, 3086)
                self.assertEqual(target.width, 7)
                self.assertEqual(target.height, 7)
                self.assertEqual(target.bands[0].datatype(), source.bands[0].datatype())
                self.assertAlmostEqual(target.origin[0], 9124842.791079799, 3)
                self.assertAlmostEqual(target.origin[1], 1589911.6476407414, 3)
                self.assertAlmostEqual(target.scale[0], 223824.82664250192, 3)
                self.assertAlmostEqual(target.scale[1], -223824.82664250192, 3)
                self.assertEqual(target.skew, [0, 0])

                result = target.bands[0].data()
                if numpy:
                    result = result.flatten().tolist()
                # The reprojection of a raster that spans over a large area
                # skews the data matrix and might introduce nodata values.
                self.assertEqual(
                    result,
                    [
                        ndv,
                        ndv,
                        ndv,
                        ndv,
                        4,
                        ndv,
                        ndv,
                        ndv,
                        ndv,
                        2,
                        3,
                        9,
                        ndv,
                        ndv,
                        ndv,
                        1,
                        2,
                        8,
                        13,
                        19,
                        ndv,
                        0,
                        6,
                        6,
                        12,
                        18,
                        18,
                        24,
                        ndv,
                        10,
                        11,
                        16,
                        22,
                        23,
                        ndv,
                        ndv,
                        ndv,
                        15,
                        21,
                        22,
                        ndv,
                        ndv,
                        ndv,
                        ndv,
                        20,
                        ndv,
                        ndv,
                        ndv,
                        ndv,
                    ],
                )