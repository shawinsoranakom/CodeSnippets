def test_compressed_file_based_raster_creation(self):
        rstfile = NamedTemporaryFile(suffix=".tif")
        # Make a compressed copy of an existing raster.
        compressed = self.rs.warp(
            {"papsz_options": {"compress": "packbits"}, "name": rstfile.name}
        )
        # Check physically if compression worked.
        self.assertLess(os.path.getsize(compressed.name), os.path.getsize(self.rs.name))
        # Create file-based raster with options from scratch.
        papsz_options = {
            "compress": "packbits",
            "blockxsize": 23,
            "blockysize": 23,
        }
        if GDAL_VERSION < (3, 7):
            datatype = 1
            papsz_options["pixeltype"] = "signedbyte"
        else:
            datatype = 14
        compressed = GDALRaster(
            {
                "datatype": datatype,
                "driver": "tif",
                "name": rstfile.name,
                "width": 40,
                "height": 40,
                "srid": 3086,
                "origin": (500000, 400000),
                "scale": (100, -100),
                "skew": (0, 0),
                "bands": [
                    {
                        "data": range(40 ^ 2),
                        "nodata_value": 255,
                    }
                ],
                "papsz_options": papsz_options,
            }
        )
        # Check if options used on creation are stored in metadata.
        # Reopening the raster ensures that all metadata has been written
        # to the file.
        compressed = GDALRaster(compressed.name)
        self.assertEqual(
            compressed.metadata["IMAGE_STRUCTURE"]["COMPRESSION"],
            "PACKBITS",
        )
        self.assertEqual(compressed.bands[0].datatype(), datatype)
        if GDAL_VERSION < (3, 7):
            self.assertEqual(
                compressed.bands[0].metadata["IMAGE_STRUCTURE"]["PIXELTYPE"],
                "SIGNEDBYTE",
            )
        self.assertIn("Block=40x23", compressed.info)