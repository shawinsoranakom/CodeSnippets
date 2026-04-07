def test_alter_field_remove_spatial_index(self):
        if not self.has_spatial_indexes:
            self.skipTest("No support for Spatial indexes")

        self.assertSpatialIndexExists("gis_neighborhood", "geom")

        self.alter_gis_model(
            migrations.AlterField,
            "Neighborhood",
            "geom",
            fields.MultiPolygonField,
            field_class_kwargs={"spatial_index": False},
        )
        self.assertSpatialIndexNotExists("gis_neighborhood", "geom")