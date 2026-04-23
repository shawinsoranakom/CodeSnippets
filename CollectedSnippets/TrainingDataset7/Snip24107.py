def test_raster_transform_clone(self):
        with mock.patch.object(GDALRaster, "clone") as mocked_clone:
            # Create in file based raster.
            rstfile = NamedTemporaryFile(suffix=".tif")
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
                            "nodata_value": 99,
                        }
                    ],
                }
            )
            # transform() returns a clone because it is the same SRID and
            # driver.
            source.transform(4326)
            self.assertEqual(mocked_clone.call_count, 1)