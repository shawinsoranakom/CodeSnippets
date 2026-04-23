def test_alter_field_nullable_with_spatial_index(self):
        if not self.has_spatial_indexes:
            self.skipTest("No support for Spatial indexes")

        self.alter_gis_model(
            migrations.AddField,
            "Neighborhood",
            "point",
            fields.PointField,
            field_class_kwargs={"spatial_index": False, "null": True},
        )
        # MySQL doesn't support spatial indexes on NULL columns.
        self.assertSpatialIndexNotExists("gis_neighborhood", "point")

        self.alter_gis_model(
            migrations.AlterField,
            "Neighborhood",
            "point",
            fields.PointField,
            field_class_kwargs={"spatial_index": True, "null": True},
        )
        self.assertSpatialIndexNotExists("gis_neighborhood", "point")

        self.alter_gis_model(
            migrations.AlterField,
            "Neighborhood",
            "point",
            fields.PointField,
            field_class_kwargs={"spatial_index": False, "null": True},
        )
        self.assertSpatialIndexNotExists("gis_neighborhood", "point")