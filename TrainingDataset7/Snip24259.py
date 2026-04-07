def test_raw_sql_query(self):
        "Testing raw SQL query."
        cities1 = City.objects.all()
        point_select = connection.ops.select % "point"
        cities2 = list(
            City.objects.raw(
                "select id, name, %s as point from geoapp_city" % point_select
            )
        )
        self.assertEqual(len(cities1), len(cities2))
        with self.assertNumQueries(0):  # Ensure point isn't deferred.
            self.assertIsInstance(cities2[0].point, Point)