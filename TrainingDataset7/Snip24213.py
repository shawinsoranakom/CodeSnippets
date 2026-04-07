def test_num_geom(self):
        # Both 'countries' only have two geometries.
        for c in Country.objects.annotate(num_geom=functions.NumGeometries("mpoly")):
            self.assertEqual(2, c.num_geom)

        qs = City.objects.filter(point__isnull=False).annotate(
            num_geom=functions.NumGeometries("point")
        )
        for city in qs:
            # The results for the number of geometries on non-collections
            # depends on the database.
            if connection.ops.mysql or connection.ops.mariadb:
                self.assertIsNone(city.num_geom)
            else:
                self.assertEqual(1, city.num_geom)