def test_ndarray_getbuf(self):
        requests = (
            # distinct flags
            PyBUF_INDIRECT, PyBUF_STRIDES, PyBUF_ND, PyBUF_SIMPLE,
            PyBUF_C_CONTIGUOUS, PyBUF_F_CONTIGUOUS, PyBUF_ANY_CONTIGUOUS,
            # compound requests
            PyBUF_FULL, PyBUF_FULL_RO,
            PyBUF_RECORDS, PyBUF_RECORDS_RO,
            PyBUF_STRIDED, PyBUF_STRIDED_RO,
            PyBUF_CONTIG, PyBUF_CONTIG_RO,
        )
        # items and format
        items_fmt = (
            ([True if x % 2 else False for x in range(12)], '?'),
            ([1,2,3,4,5,6,7,8,9,10,11,12], 'b'),
            ([1,2,3,4,5,6,7,8,9,10,11,12], 'B'),
            ([(2**31-x) if x % 2 else (-2**31+x) for x in range(12)], 'l')
        )
        # shape, strides, offset
        structure = (
            ([], [], 0),
            ([1,3,1], [], 0),
            ([12], [], 0),
            ([12], [-1], 11),
            ([6], [2], 0),
            ([6], [-2], 11),
            ([3, 4], [], 0),
            ([3, 4], [-4, -1], 11),
            ([2, 2], [4, 1], 4),
            ([2, 2], [-4, -1], 8)
        )
        # ndarray creation flags
        ndflags = (
            0, ND_WRITABLE, ND_FORTRAN, ND_FORTRAN|ND_WRITABLE,
            ND_PIL, ND_PIL|ND_WRITABLE
        )
        # flags that can actually be used as flags
        real_flags = (0, PyBUF_WRITABLE, PyBUF_FORMAT,
                      PyBUF_WRITABLE|PyBUF_FORMAT)

        for items, fmt in items_fmt:
            itemsize = struct.calcsize(fmt)
            for shape, strides, offset in structure:
                strides = [v * itemsize for v in strides]
                offset *= itemsize
                for flags in ndflags:

                    if strides and (flags&ND_FORTRAN):
                        continue
                    if not shape and (flags&ND_PIL):
                        continue

                    _items = items if shape else items[0]
                    ex1 = ndarray(_items, format=fmt, flags=flags,
                                  shape=shape, strides=strides, offset=offset)
                    ex2 = ex1[::-2] if shape else None

                    m1 = memoryview(ex1)
                    if ex2:
                        m2 = memoryview(ex2)
                    if ex1.ndim == 0 or (ex1.ndim == 1 and shape and strides):
                        self.assertEqual(m1, ex1)
                    if ex2 and ex2.ndim == 1 and shape and strides:
                        self.assertEqual(m2, ex2)

                    for req in requests:
                        for bits in real_flags:
                            self.verify_getbuf(ex1, ex1, req|bits)
                            self.verify_getbuf(ex1, m1, req|bits)
                            if ex2:
                                self.verify_getbuf(ex2, ex2, req|bits,
                                                   sliced=True)
                                self.verify_getbuf(ex2, m2, req|bits,
                                                   sliced=True)

        items = [1,2,3,4,5,6,7,8,9,10,11,12]

        # ND_GETBUF_FAIL
        ex = ndarray(items, shape=[12], flags=ND_GETBUF_FAIL)
        self.assertRaises(BufferError, ndarray, ex)

        # Request complex structure from a simple exporter. In this
        # particular case the test object is not PEP-3118 compliant.
        base = ndarray([9], [1])
        ex = ndarray(base, getbuf=PyBUF_SIMPLE)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_WRITABLE)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_ND)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_STRIDES)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_C_CONTIGUOUS)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_F_CONTIGUOUS)
        self.assertRaises(BufferError, ndarray, ex, getbuf=PyBUF_ANY_CONTIGUOUS)
        nd = ndarray(ex, getbuf=PyBUF_SIMPLE)

        # Issue #22445: New precise contiguity definition.
        for shape in [1,12,1], [7,0,7]:
            for order in 0, ND_FORTRAN:
                ex = ndarray(items, shape=shape, flags=order|ND_WRITABLE)
                self.assertTrue(is_contiguous(ex, 'F'))
                self.assertTrue(is_contiguous(ex, 'C'))

                for flags in requests:
                    nd = ndarray(ex, getbuf=flags)
                    self.assertTrue(is_contiguous(nd, 'F'))
                    self.assertTrue(is_contiguous(nd, 'C'))