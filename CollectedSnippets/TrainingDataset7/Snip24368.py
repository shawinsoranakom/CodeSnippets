def test_point_list_assignment(self):
        p = Point(0, 0)

        p[:] = (1, 2, 3)
        self.assertEqual(p, Point(1, 2, 3))

        p[:] = ()
        self.assertEqual(p.wkt, Point())

        p[:] = (1, 2)
        self.assertEqual(p.wkt, Point(1, 2))

        with self.assertRaisesMessage(ValueError, "Must have at least 2 items"):
            p[:] = (1,)
        with self.assertRaisesMessage(ValueError, "Cannot have more than 3 items"):
            p[:] = (1, 2, 3, 4, 5)