def test_add_raster_field(self):
        """
        Test the AddField operation with a raster-enabled column.
        """
        self.alter_gis_model(
            migrations.AddField, "Neighborhood", "heatmap", fields.RasterField
        )
        self.assertColumnExists("gis_neighborhood", "heatmap")

        # Test spatial indices when available
        if self.has_spatial_indexes:
            self.assertSpatialIndexExists("gis_neighborhood", "heatmap", raster=True)