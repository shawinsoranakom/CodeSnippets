def test_make_line(self):
        """
        Testing the `MakeLine` aggregate.
        """
        if not connection.features.supports_make_line_aggr:
            with self.assertRaises(NotSupportedError):
                City.objects.aggregate(MakeLine("point"))
            return

        # MakeLine on an inappropriate field returns simply None
        self.assertIsNone(State.objects.aggregate(MakeLine("poly"))["poly__makeline"])
        # Reference query:
        # SELECT AsText(ST_MakeLine(geoapp_city.point)) FROM geoapp_city;
        line = City.objects.aggregate(MakeLine("point"))["point__makeline"]
        ref_points = City.objects.values_list("point", flat=True)
        self.assertIsInstance(line, LineString)
        self.assertEqual(len(line), ref_points.count())
        # Compare pairs of manually sorted points, as the default ordering is
        # flaky.
        for point, ref_city in zip(sorted(line), sorted(ref_points)):
            point_x, point_y = point
            self.assertAlmostEqual(point_x, ref_city.x, 5)
            self.assertAlmostEqual(point_y, ref_city.y, 5)