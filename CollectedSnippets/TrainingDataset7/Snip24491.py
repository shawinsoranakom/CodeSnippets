def test_add_blank_raster_field(self):
        """
        Should be able to add a RasterField with blank=True.
        """
        self.alter_gis_model(
            migrations.AddField,
            "Neighborhood",
            "heatmap",
            fields.RasterField,
            field_class_kwargs={"blank": True},
        )
        self.assertColumnExists("gis_neighborhood", "heatmap")

        # Test spatial indices when available
        if self.has_spatial_indexes:
            self.assertSpatialIndexExists("gis_neighborhood", "heatmap", raster=True)