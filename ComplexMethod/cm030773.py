def test_ndarray_random_slice_assign(self):
        # valid slice assignments
        for _ in range(ITERATIONS):
            for fmt in fmtdict['@']:
                itemsize = struct.calcsize(fmt)

                lshape, rshape, lslices, rslices = \
                    rand_aligned_slices(maxdim=MAXDIM, maxshape=MAXSHAPE)
                tl = rand_structure(itemsize, True, shape=lshape)
                tr = rand_structure(itemsize, True, shape=rshape)
                self.assertTrue(verify_structure(*tl))
                self.assertTrue(verify_structure(*tr))
                litems = randitems_from_structure(fmt, tl)
                ritems = randitems_from_structure(fmt, tr)

                xl = ndarray_from_structure(litems, fmt, tl)
                xr = ndarray_from_structure(ritems, fmt, tr)
                xl[lslices] = xr[rslices]
                xllist = xl.tolist()
                xrlist = xr.tolist()

                ml = memoryview(xl)
                mr = memoryview(xr)
                self.assertEqual(ml.tolist(), xllist)
                self.assertEqual(mr.tolist(), xrlist)

                if tl[2] > 0 and tr[2] > 0:
                    # ndim > 0: test against suboffsets representation.
                    yl = ndarray_from_structure(litems, fmt, tl, flags=ND_PIL)
                    yr = ndarray_from_structure(ritems, fmt, tr, flags=ND_PIL)
                    yl[lslices] = yr[rslices]
                    yllist = yl.tolist()
                    yrlist = yr.tolist()
                    self.assertEqual(xllist, yllist)
                    self.assertEqual(xrlist, yrlist)

                    ml = memoryview(yl)
                    mr = memoryview(yr)
                    self.assertEqual(ml.tolist(), yllist)
                    self.assertEqual(mr.tolist(), yrlist)

                if numpy_array:
                    if 0 in lshape or 0 in rshape:
                        continue # https://github.com/numpy/numpy/issues/2503

                    zl = numpy_array_from_structure(litems, fmt, tl)
                    zr = numpy_array_from_structure(ritems, fmt, tr)
                    zl[lslices] = zr[rslices]

                    if not is_overlapping(tl) and not is_overlapping(tr):
                        # Slice assignment of overlapping structures
                        # is undefined in NumPy.
                        self.verify(xl, obj=None,
                                    itemsize=zl.itemsize, fmt=fmt, readonly=False,
                                    ndim=zl.ndim, shape=zl.shape,
                                    strides=zl.strides, lst=zl.tolist())

                    self.verify(xr, obj=None,
                                itemsize=zr.itemsize, fmt=fmt, readonly=False,
                                ndim=zr.ndim, shape=zr.shape,
                                strides=zr.strides, lst=zr.tolist())