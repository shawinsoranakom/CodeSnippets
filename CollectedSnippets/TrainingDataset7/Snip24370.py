def test_linearring_list_assignment(self):
        ls = LinearRing((0, 0), (0, 1), (1, 1), (0, 0))

        ls[:] = ()
        self.assertEqual(ls, LinearRing())

        ls[:] = ((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))
        self.assertEqual(ls, LinearRing((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))

        with self.assertRaisesMessage(ValueError, "Must have at least 4 items"):
            ls[:] = ((0, 0), (1, 1), (2, 2))