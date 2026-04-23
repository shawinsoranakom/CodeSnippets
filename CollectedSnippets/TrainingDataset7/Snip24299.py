def test_operators_functions_unavailable_for_geography(self):
        """
        Geography fields are cast to geometry if the relevant operators or
        functions are not available.
        """
        z = Zipcode.objects.get(code="77002")
        point_field = "%s.%s::geometry" % (
            connection.ops.quote_name(City._meta.db_table),
            connection.ops.quote_name("point"),
        )
        # ST_Within.
        qs = City.objects.filter(point__within=z.poly)
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(qs.count(), 1)
        self.assertIn(f"ST_Within({point_field}", ctx.captured_queries[0]["sql"])
        # @ operator.
        qs = City.objects.filter(point__contained=z.poly)
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(qs.count(), 1)
        self.assertIn(f"{point_field} @", ctx.captured_queries[0]["sql"])
        # ~= operator.
        htown = City.objects.get(name="Houston")
        qs = City.objects.filter(point__exact=htown.point)
        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(qs.count(), 1)
        self.assertIn(f"{point_field} ~=", ctx.captured_queries[0]["sql"])