def test_normalize(self):
        multipoint = MultiPoint(Point(0, 0), Point(2, 2), Point(1, 1))
        normalized = MultiPoint(Point(2, 2), Point(1, 1), Point(0, 0))
        # Geometry is normalized in-place and nothing is returned.
        multipoint_1 = multipoint.clone()
        self.assertIsNone(multipoint_1.normalize())
        self.assertEqual(multipoint_1, normalized)
        # If the `clone` keyword is set, then the geometry is not modified and
        # a normalized clone of the geometry is returned instead.
        multipoint_2 = multipoint.normalize(clone=True)
        self.assertEqual(multipoint_2, normalized)
        self.assertNotEqual(multipoint, normalized)