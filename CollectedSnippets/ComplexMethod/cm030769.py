def test_ndarray_slice_multidim(self):
        shape_t = (2, 3, 5)
        ndim = len(shape_t)
        nitems = prod(shape_t)
        for shape in permutations(shape_t):

            fmt, items, _ = randitems(nitems)
            itemsize = struct.calcsize(fmt)

            for flags in (0, ND_PIL):
                nd = ndarray(items, shape=shape, format=fmt, flags=flags)
                lst = carray(items, shape)

                for slices in rslices_ndim(ndim, shape):

                    listerr = None
                    try:
                        sliced = multislice(lst, slices)
                    except Exception as e:
                        listerr = e.__class__

                    nderr = None
                    try:
                        ndsliced = nd[slices]
                    except Exception as e:
                        nderr = e.__class__

                    if nderr or listerr:
                        self.assertIs(nderr, listerr)
                    else:
                        self.assertEqual(ndsliced.tolist(), sliced)