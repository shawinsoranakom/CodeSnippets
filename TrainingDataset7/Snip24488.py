def test_geom_col_name(self):
        self.assertEqual(
            GeometryColumns.geom_col_name(),
            "column_name" if connection.ops.oracle else "f_geometry_column",
        )