def test_create_model_spatial_index(self):
        if not self.has_spatial_indexes:
            self.skipTest("No support for Spatial indexes")

        self.assertSpatialIndexExists("gis_neighborhood", "geom")

        if connection.features.supports_raster:
            self.assertSpatialIndexExists("gis_neighborhood", "rast", raster=True)