def test_raster_metadata_property(self):
        data = self.rs.metadata
        self.assertEqual(data["DEFAULT"], {"AREA_OR_POINT": "Area"})
        self.assertEqual(data["IMAGE_STRUCTURE"], {"INTERLEAVE": "BAND"})

        # Create file-based raster from scratch
        source = GDALRaster(
            {
                "datatype": 1,
                "width": 2,
                "height": 2,
                "srid": 4326,
                "bands": [{"data": range(4), "nodata_value": 99}],
            }
        )
        # Set metadata on raster and on a band.
        metadata = {
            "DEFAULT": {"OWNER": "Django", "VERSION": "1.0", "AREA_OR_POINT": "Point"},
        }
        source.metadata = metadata
        source.bands[0].metadata = metadata
        self.assertEqual(source.metadata["DEFAULT"], metadata["DEFAULT"])
        self.assertEqual(source.bands[0].metadata["DEFAULT"], metadata["DEFAULT"])
        # Update metadata on raster.
        metadata = {
            "DEFAULT": {"VERSION": "2.0"},
        }
        source.metadata = metadata
        self.assertEqual(source.metadata["DEFAULT"]["VERSION"], "2.0")
        # Remove metadata on raster.
        metadata = {
            "DEFAULT": {"OWNER": None},
        }
        source.metadata = metadata
        self.assertNotIn("OWNER", source.metadata["DEFAULT"])