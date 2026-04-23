def test_raster_transform_clone_name(self):
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
        clone_name = rstfile.name + "_respect_name.GTiff"
        target = source.transform(4326, name=clone_name)
        self.assertEqual(target.name, clone_name)