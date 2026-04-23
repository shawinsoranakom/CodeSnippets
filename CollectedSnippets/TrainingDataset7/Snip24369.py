def test_linestring_list_assignment(self):
        ls = LineString((0, 0), (1, 1))

        ls[:] = ()
        self.assertEqual(ls, LineString())

        ls[:] = ((0, 0), (1, 1), (2, 2))
        self.assertEqual(ls, LineString((0, 0), (1, 1), (2, 2)))

        with self.assertRaisesMessage(ValueError, "Must have at least 2 items"):
            ls[:] = (1,)