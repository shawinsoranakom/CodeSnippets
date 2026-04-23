def test_ndarray_slice_assign_single(self):
        for fmt, items, _ in iter_format(5):
            for lslice in genslices(5):
                for rslice in genslices(5):
                    for flags in (0, ND_PIL):

                        f = flags|ND_WRITABLE
                        nd = ndarray(items, shape=[5], format=fmt, flags=f)
                        ex = ndarray(items, shape=[5], format=fmt, flags=f)
                        mv = memoryview(ex)

                        lsterr = None
                        diff_structure = None
                        lst = items[:]
                        try:
                            lval = lst[lslice]
                            rval = lst[rslice]
                            lst[lslice] = lst[rslice]
                            diff_structure = len(lval) != len(rval)
                        except Exception as e:
                            lsterr = e.__class__

                        nderr = None
                        try:
                            nd[lslice] = nd[rslice]
                        except Exception as e:
                            nderr = e.__class__

                        if diff_structure: # ndarray cannot change shape
                            self.assertIs(nderr, ValueError)
                        else:
                            self.assertEqual(nd.tolist(), lst)
                            self.assertIs(nderr, lsterr)

                        if not is_memoryview_format(fmt):
                            continue

                        mverr = None
                        try:
                            mv[lslice] = mv[rslice]
                        except Exception as e:
                            mverr = e.__class__

                        if diff_structure: # memoryview cannot change shape
                            self.assertIs(mverr, ValueError)
                        else:
                            self.assertEqual(mv.tolist(), lst)
                            self.assertEqual(mv, nd)
                            self.assertIs(mverr, lsterr)
                            self.verify(mv, obj=ex,
                              itemsize=nd.itemsize, fmt=fmt, readonly=False,
                              ndim=nd.ndim, shape=nd.shape, strides=nd.strides,
                              lst=nd.tolist())