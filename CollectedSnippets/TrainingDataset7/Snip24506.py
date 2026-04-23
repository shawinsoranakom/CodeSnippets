def test_3d_columns(self):
        out = StringIO()
        call_command(
            "inspectdb",
            table_name_filter=lambda tn: tn == "inspectapp_fields3d",
            stdout=out,
        )
        output = out.getvalue()
        if connection.features.supports_geometry_field_introspection:
            self.assertIn("point = models.PointField(dim=3)", output)
            if connection.features.supports_geography:
                self.assertIn(
                    "pointg = models.PointField(geography=True, dim=3)", output
                )
            else:
                self.assertIn("pointg = models.PointField(dim=3)", output)
            self.assertIn("line = models.LineStringField(dim=3)", output)
            self.assertIn("poly = models.PolygonField(dim=3)", output)
        else:
            self.assertIn("point = models.GeometryField(", output)
            self.assertIn("pointg = models.GeometryField(", output)
            self.assertIn("line = models.GeometryField(", output)
            self.assertIn("poly = models.GeometryField(", output)