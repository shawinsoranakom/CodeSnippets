def test_linestring_iter(self):
        ls = LineString((0, 0), (1, 1))
        it = iter(ls)
        # Step into CoordSeq iterator.
        next(it)
        ls[:] = []
        with self.assertRaisesMessage(IndexError, "invalid index: 1"):
            next(it)