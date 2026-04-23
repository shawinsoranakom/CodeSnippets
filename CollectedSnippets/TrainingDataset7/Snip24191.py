def test_bounding_circle(self):
        def circle_num_points(num_seg):
            # num_seg is the number of segments per quarter circle.
            return (4 * num_seg) + 1

        if connection.ops.postgis:
            expected_area = 169
        elif connection.ops.spatialite:
            expected_area = 168
        else:  # Oracle.
            expected_area = 171
        country = Country.objects.annotate(
            circle=functions.BoundingCircle("mpoly")
        ).order_by("name")[0]
        self.assertAlmostEqual(country.circle.area, expected_area, 0)
        if connection.ops.postgis:
            # By default num_seg=48.
            self.assertEqual(country.circle.num_points, circle_num_points(48))

        tests = [12, Value(12, output_field=IntegerField())]
        for num_seq in tests:
            with self.subTest(num_seq=num_seq):
                country = Country.objects.annotate(
                    circle=functions.BoundingCircle("mpoly", num_seg=num_seq),
                ).order_by("name")[0]
                if connection.ops.postgis:
                    self.assertGreater(country.circle.area, 168.4, 0)
                    self.assertLess(country.circle.area, 169.5, 0)
                    self.assertEqual(country.circle.num_points, circle_num_points(12))
                else:
                    self.assertAlmostEqual(country.circle.area, expected_area, 0)