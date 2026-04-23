def test_linearring(self):
        "Testing LinearRing objects."
        for rr in self.geometries.linearrings:
            lr = fromstr(rr.wkt)
            with self.subTest(rr=rr):
                self.assertEqual(lr.geom_type, "LinearRing")
                self.assertEqual(lr.geom_typeid, 2)
                self.assertEqual(lr.dims, 1)
                self.assertEqual(rr.n_p, len(lr))
                self.assertIs(lr.valid, True)
                self.assertIs(lr.empty, False)

                # Creating a LinearRing from a tuple, list, and numpy array
                self.assertEqual(lr, LinearRing(lr.tuple))
                self.assertEqual(lr, LinearRing(*lr.tuple))
                self.assertEqual(lr, LinearRing([list(tup) for tup in lr.tuple]))
                if numpy:
                    self.assertEqual(lr, LinearRing(numpy.array(lr.tuple)))

        with self.assertRaisesMessage(
            ValueError, "LinearRing requires at least 4 points, got 3."
        ):
            LinearRing((0, 0), (1, 1), (0, 0))

        with self.assertRaisesMessage(
            ValueError, "LinearRing requires at least 4 points, got 1."
        ):
            LinearRing([(0, 0)])

        if numpy:
            with self.assertRaisesMessage(
                ValueError, "LinearRing requires at least 4 points, got 1."
            ):
                LinearRing(numpy.array([(0, 0)]))