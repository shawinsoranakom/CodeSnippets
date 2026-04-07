def test_file_based_raster_creation(self):
        # Prepare tempfile
        rstfile = NamedTemporaryFile(suffix=".tif")

        # Create file-based raster from scratch
        GDALRaster(
            {
                "datatype": self.rs.bands[0].datatype(),
                "driver": "tif",
                "name": rstfile.name,
                "width": 163,
                "height": 174,
                "nr_of_bands": 1,
                "srid": self.rs.srs.wkt,
                "origin": (self.rs.origin.x, self.rs.origin.y),
                "scale": (self.rs.scale.x, self.rs.scale.y),
                "skew": (self.rs.skew.x, self.rs.skew.y),
                "bands": [
                    {
                        "data": self.rs.bands[0].data(),
                        "nodata_value": self.rs.bands[0].nodata_value,
                    }
                ],
            }
        )

        # Reload newly created raster from file
        restored_raster = GDALRaster(rstfile.name)
        # Presence of TOWGS84 depend on GDAL/Proj versions.
        self.assertEqual(
            restored_raster.srs.wkt.replace("TOWGS84[0,0,0,0,0,0,0],", ""),
            self.rs.srs.wkt.replace("TOWGS84[0,0,0,0,0,0,0],", ""),
        )
        self.assertEqual(restored_raster.geotransform, self.rs.geotransform)
        if numpy:
            numpy.testing.assert_equal(
                restored_raster.bands[0].data(), self.rs.bands[0].data()
            )
        else:
            self.assertEqual(restored_raster.bands[0].data(), self.rs.bands[0].data())