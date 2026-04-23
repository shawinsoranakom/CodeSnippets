def test_geom_columns(self):
        """
        Test the geo-enabled inspectdb command.
        """
        out = StringIO()
        call_command(
            "inspectdb",
            table_name_filter=lambda tn: tn == "inspectapp_allogrfields",
            stdout=out,
        )
        output = out.getvalue()
        if connection.features.supports_geometry_field_introspection:
            self.assertIn("geom = models.PolygonField()", output)
            self.assertIn("point = models.PointField()", output)
        else:
            self.assertIn("geom = models.GeometryField(", output)
            self.assertIn("point = models.GeometryField(", output)