def test_linestring(self):
        "Testing LineString objects."
        prev = fromstr("POINT(0 0)")
        for line in self.geometries.linestrings:
            ls = fromstr(line.wkt)
            with self.subTest(line=line):
                self.assertEqual(ls.geom_type, "LineString")
                self.assertEqual(ls.geom_typeid, 1)
                self.assertEqual(ls.dims, 1)
                self.assertIs(ls.empty, False)
                self.assertIs(ls.ring, False)
                if hasattr(line, "centroid"):
                    self.assertEqual(line.centroid, ls.centroid.tuple)
                if hasattr(line, "tup"):
                    self.assertEqual(line.tup, ls.tuple)

                self.assertEqual(ls, fromstr(line.wkt))
                self.assertIs(ls == prev, False)  # Use assertIs() to test __eq__.
                ls_len = len(ls)
                msg = f"invalid index: {ls_len}"
                with self.assertRaisesMessage(IndexError, msg):
                    ls.__getitem__(ls_len)
                prev = ls

                # Creating a LineString from a tuple, list, and numpy array
                self.assertEqual(ls, LineString(ls.tuple))  # tuple
                self.assertEqual(ls, LineString(*ls.tuple))  # as individual arguments
                self.assertEqual(
                    ls, LineString([list(tup) for tup in ls.tuple])
                )  # as list
                # Point individual arguments
                self.assertEqual(
                    ls.wkt, LineString(*tuple(Point(tup) for tup in ls.tuple)).wkt
                )
                if numpy:
                    self.assertEqual(
                        ls, LineString(numpy.array(ls.tuple))
                    )  # as numpy array

        with self.assertRaisesMessage(
            TypeError, "Each coordinate should be a sequence (list or tuple)"
        ):
            LineString((0, 0))

        with self.assertRaisesMessage(
            ValueError, "LineString requires at least 2 points, got 1."
        ):
            LineString([(0, 0)])

        if numpy:
            with self.assertRaisesMessage(
                ValueError, "LineString requires at least 2 points, got 1."
            ):
                LineString(numpy.array([(0, 0)]))

        with mock.patch("django.contrib.gis.geos.linestring.numpy", False):
            with self.assertRaisesMessage(
                TypeError, "Invalid initialization input for LineStrings."
            ):
                LineString("wrong input")

        # Test __iter__().
        self.assertEqual(
            list(LineString((0, 0), (1, 1), (2, 2))), [(0, 0), (1, 1), (2, 2)]
        )