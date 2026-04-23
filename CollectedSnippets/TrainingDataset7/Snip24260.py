def test_gis_query_as_string(self):
        """GIS queries can be represented as strings."""
        query = City.objects.filter(point__within=Polygon.from_bbox((0, 0, 2, 2)))
        self.assertIn(
            connection.ops.quote_name(City._meta.db_table),
            str(query.query),
        )