def test_polygon_list_assignment(self):
        pol = Polygon()

        pol[:] = (((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)),)
        self.assertEqual(
            pol,
            Polygon(
                ((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)),
            ),
        )

        pol[:] = ()
        self.assertEqual(pol, Polygon())