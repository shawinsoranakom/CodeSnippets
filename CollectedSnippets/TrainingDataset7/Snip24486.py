def test_add_geom_field(self):
        """
        Test the AddField operation with a geometry-enabled column.
        """
        self.alter_gis_model(
            migrations.AddField, "Neighborhood", "path", fields.LineStringField
        )
        self.assertColumnExists("gis_neighborhood", "path")

        # Test GeometryColumns when available
        if HAS_GEOMETRY_COLUMNS:
            self.assertGeometryColumnsCount(2)

        # Test spatial indices when available
        if self.has_spatial_indexes:
            self.assertSpatialIndexExists("gis_neighborhood", "path")