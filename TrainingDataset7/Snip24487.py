def test_remove_geom_field_nullable_with_index(self):
        # MySQL doesn't support spatial indexes on NULL columns.
        with self.assertNumQueries(1) as ctx:
            self.alter_gis_model(
                migrations.AddField,
                "Neighborhood",
                "path",
                fields.LineStringField,
                field_class_kwargs={"null": True},
            )
        self.assertColumnExists("gis_neighborhood", "path")
        self.assertNotIn("CREATE SPATIAL INDEX", ctx.captured_queries[0]["sql"])

        with self.assertNumQueries(1), self.assertNoLogs("django.contrib.gis", "ERROR"):
            self.alter_gis_model(migrations.RemoveField, "Neighborhood", "path")
        self.assertColumnNotExists("gis_neighborhood", "path")