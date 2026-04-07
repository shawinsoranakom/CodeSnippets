def test_add_blank_geom_field(self):
        """
        Should be able to add a GeometryField with blank=True.
        """
        self.alter_gis_model(
            migrations.AddField,
            "Neighborhood",
            "path",
            fields.LineStringField,
            field_class_kwargs={"blank": True},
        )
        self.assertColumnExists("gis_neighborhood", "path")

        # Test GeometryColumns when available
        if HAS_GEOMETRY_COLUMNS:
            self.assertGeometryColumnsCount(2)

        # Test spatial indices when available
        if self.has_spatial_indexes:
            self.assertSpatialIndexExists("gis_neighborhood", "path")