def test_ndarray_index_getitem_multidim(self):
        shape_t = (2, 3, 5)
        nitems = prod(shape_t)
        for shape in permutations(shape_t):

            fmt, items, _ = randitems(nitems)

            for flags in (0, ND_PIL):
                # C array
                nd = ndarray(items, shape=shape, format=fmt, flags=flags)
                lst = carray(items, shape)

                for i in range(-shape[0], shape[0]):
                    self.assertEqual(lst[i], nd[i].tolist())
                    for j in range(-shape[1], shape[1]):
                        self.assertEqual(lst[i][j], nd[i][j].tolist())
                        for k in range(-shape[2], shape[2]):
                            self.assertEqual(lst[i][j][k], nd[i][j][k])

                # Fortran array
                nd = ndarray(items, shape=shape, format=fmt,
                             flags=flags|ND_FORTRAN)
                lst = farray(items, shape)

                for i in range(-shape[0], shape[0]):
                    self.assertEqual(lst[i], nd[i].tolist())
                    for j in range(-shape[1], shape[1]):
                        self.assertEqual(lst[i][j], nd[i][j].tolist())
                        for k in range(shape[2], shape[2]):
                            self.assertEqual(lst[i][j][k], nd[i][j][k])