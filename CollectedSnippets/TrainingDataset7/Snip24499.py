def test_add_3d_field_opclass(self):
        if not connection.ops.postgis:
            self.skipTest("PostGIS-specific test.")

        self.alter_gis_model(
            migrations.AddField,
            "Neighborhood",
            "point3d",
            field_class=fields.PointField,
            field_class_kwargs={"dim": 3},
        )
        self.assertColumnExists("gis_neighborhood", "point3d")
        self.assertSpatialIndexExists("gis_neighborhood", "point3d")

        with connection.cursor() as cursor:
            index_name = "gis_neighborhood_point3d_113bc868_id"
            cursor.execute(self.get_opclass_query, [index_name])
            self.assertEqual(
                cursor.fetchall(),
                [("gist_geometry_ops_nd", index_name)],
            )