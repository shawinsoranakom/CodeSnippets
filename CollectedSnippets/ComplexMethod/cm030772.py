def test_ndarray_random(self):
        # construction of valid arrays
        for _ in range(ITERATIONS):
            for fmt in fmtdict['@']:
                itemsize = struct.calcsize(fmt)

                t = rand_structure(itemsize, True, maxdim=MAXDIM,
                                   maxshape=MAXSHAPE)
                self.assertTrue(verify_structure(*t))
                items = randitems_from_structure(fmt, t)

                x = ndarray_from_structure(items, fmt, t)
                xlist = x.tolist()

                mv = memoryview(x)
                if is_memoryview_format(fmt):
                    mvlist = mv.tolist()
                    self.assertEqual(mvlist, xlist)

                if t[2] > 0:
                    # ndim > 0: test against suboffsets representation.
                    y = ndarray_from_structure(items, fmt, t, flags=ND_PIL)
                    ylist = y.tolist()
                    self.assertEqual(xlist, ylist)

                    mv = memoryview(y)
                    if is_memoryview_format(fmt):
                        self.assertEqual(mv, y)
                        mvlist = mv.tolist()
                        self.assertEqual(mvlist, ylist)

                if numpy_array:
                    shape = t[3]
                    if 0 in shape:
                        continue # https://github.com/numpy/numpy/issues/2503
                    z = numpy_array_from_structure(items, fmt, t)
                    self.verify(x, obj=None,
                                itemsize=z.itemsize, fmt=fmt, readonly=False,
                                ndim=z.ndim, shape=z.shape, strides=z.strides,
                                lst=z.tolist())