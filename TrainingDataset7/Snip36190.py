def test_sort(self):
        d = ImmutableList(range(10))

        # AttributeError: ImmutableList object is immutable.
        with self.assertRaisesMessage(
            AttributeError, "ImmutableList object is immutable."
        ):
            d.sort()

        self.assertEqual(repr(d), "(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)")