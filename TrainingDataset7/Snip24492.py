def test_remove_geom_field(self):
        """
        Test the RemoveField operation with a geometry-enabled column.
        """
        self.alter_gis_model(migrations.RemoveField, "Neighborhood", "geom")
        self.assertColumnNotExists("gis_neighborhood", "geom")

        # Test GeometryColumns when available
        if HAS_GEOMETRY_COLUMNS:
            self.assertGeometryColumnsCount(0)